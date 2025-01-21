/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
*/

/*
    This is an LD_PRELOAD interposer library to connect /dev/input/jsX devices to unix domain sockets.
    The unix domain sockets are used to send/receive joystick cofiguration and events.

    The open() SYSCALL is interposed to initiate the socket connection
    and recieve the joystick configuration like name, button and axes mappings.

    The ioctl() SYSCALL is interposed to fake the behavior of a input event character device.
    These ioctl requests were mostly reverse engineered from the joystick.h source and using the jstest command to test.

    Note that some applications list the /dev/input/* directory to discover JS devices, to solve for this, create empty files at the following paths:
        sudo mkdir -pm1777 /dev/input
        sudo touch /dev/input/{js0,js1,js2,js3}
        sudo chmod 777 /dev/input/js*

    For SDL2 support, only 1 interposed joystick device is supported at a time and the following env var must be set:
        export SDL_JOYSTICK_DEVICE=/dev/input/js0
*/

#define _GNU_SOURCE // Required for RTLD_NEXT

#include <dlfcn.h>
#include <stdio.h>
#include <stdarg.h>
#include <fcntl.h>
#include <string.h>
#include <stdint.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <sys/un.h>
#include <sys/ioctl.h>
#include <sys/epoll.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <linux/joystick.h>
#include <linux/input-event-codes.h>

#define LOG_FILE "/tmp/selkies_js.log"

// Timeout to wait for unix domain socket to exist and connect.
#define SOCKET_CONNECT_TIMEOUT_MS 250

#define JS0_DEVICE_PATH "/dev/input/js0"
#define JS0_SOCKET_PATH "/tmp/selkies_js0.sock"
#define JS1_DEVICE_PATH "/dev/input/js1"
#define JS1_SOCKET_PATH "/tmp/selkies_js1.sock"
#define JS2_DEVICE_PATH "/dev/input/js2"
#define JS2_SOCKET_PATH "/tmp/selkies_js2.sock"
#define JS3_DEVICE_PATH "/dev/input/js3"
#define JS3_SOCKET_PATH "/tmp/selkies_js3.sock"
#define NUM_JS_INTERPOSERS 4

// Define the function signature for the original open and ioctl syscalls
typedef int (*open_func_t)(const char *pathname, int flags, ...);
typedef int (*open64_func_t)(const char *pathname, int flags, ...);
typedef int (*ioctl_func_t)(int fd, unsigned long request, ...);

static int (*real_epoll_ctl)(int epfd, int op, int fd, struct epoll_event *event) = NULL;

// Function pointers to the original open and ioctl syscalls
static open_func_t real_open = NULL;
static open64_func_t real_open64 = NULL;
static ioctl_func_t real_ioctl = NULL;

// type definition for correction struct
typedef struct js_corr js_corr_t;

typedef struct
{
    char name[255];        // Name of the controller
    uint16_t num_btns;     // Number of buttons
    uint16_t num_axes;     // Number of axes
    uint16_t btn_map[512]; // Button map
    uint8_t axes_map[64];  // axes map
} js_config_t;

// Struct for storing information about each interposed joystick device.
typedef struct
{
    char open_dev_name[255];
    char socket_path[255];
    int sockfd;
    js_corr_t corr;
    js_config_t js_config;
} js_interposer_t;

static js_interposer_t interposers[NUM_JS_INTERPOSERS] = {
    {
        open_dev_name : JS0_DEVICE_PATH,
        socket_path : JS0_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
    {
        open_dev_name : JS1_DEVICE_PATH,
        socket_path : JS1_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
    {
        open_dev_name : JS2_DEVICE_PATH,
        socket_path : JS2_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
    {
        open_dev_name : JS3_DEVICE_PATH,
        socket_path : JS3_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
};

static FILE *log_file_fd = NULL;
void init_log_file()
{
    if (log_file_fd != NULL)
        return;
    log_file_fd = fopen(LOG_FILE, "a");
}

// Log messages from the interposer go to stderr
#define LOG_INFO "[INFO]"
#define LOG_WARN "[WARN]"
#define LOG_ERROR "[ERROR]"
static void interposer_log(const char *level, const char *msg, ...)
{
    init_log_file();
    va_list argp;
    va_start(argp, msg);
    fprintf(log_file_fd, "[%lu][Selkies Joystick Interposer]%s ", (unsigned long)time(NULL), level);
    vfprintf(log_file_fd, msg, argp);
    fprintf(log_file_fd, "\n");
    fflush(log_file_fd);
    va_end(argp);
}

void init_real_ioctl()
{
    if (real_ioctl != NULL)
        return;
    real_ioctl = (ioctl_func_t)dlsym(RTLD_NEXT, "ioctl");
}

void init_real_open()
{
    if (real_open != NULL)
        return;
    real_open = (open_func_t)dlsym(RTLD_NEXT, "open");
}

void init_real_open64()
{
    if (real_open64 != NULL)
        return;
    real_open64 = (open64_func_t)dlsym(RTLD_NEXT, "open64");
}

void init_real_epoll_ctl()
{
    if (real_epoll_ctl != NULL)
        return;
    real_epoll_ctl = dlsym(RTLD_NEXT, "epoll_ctl");
}

int make_nonblocking(int sockfd)
{
    // Get the current file descriptor flags
    int flags = fcntl(sockfd, F_GETFL, 0);
    if (flags == -1)
    {
        interposer_log(LOG_ERROR, "Failed to get current flags on socket fd to make non-blocking");
        return -1;
    }

    // Set the non-blocking flag
    flags |= O_NONBLOCK;
    if (fcntl(sockfd, F_SETFL, flags) == -1)
    {
        interposer_log(LOG_ERROR, "Failed to set flags on socket fd to make non-blocking");
        return -1;
    }

    return 0; // Success
}

int read_config(int fd, js_config_t *js_config)
{
    ssize_t bytesRead;

    // Read config from the file descriptor
    bytesRead = read(fd, js_config, sizeof(js_config_t));

    if (bytesRead == -1)
    {
        interposer_log(LOG_ERROR, "Failed to read config");
        return -1;
    }
    else if (bytesRead == 0)
    {
        interposer_log(LOG_ERROR, "Failed to read config, reached socket EOF and 0 bytes read");
        // End of file reached
        return -1;
    }

    interposer_log(LOG_INFO, "Read config from socket:");
    interposer_log(LOG_INFO, "  name: %s", js_config->name);
    interposer_log(LOG_INFO, "  num buttons: %d", js_config->num_btns);
    interposer_log(LOG_INFO, "  num axes: %d", js_config->num_axes);

    return 0;
}

int interposer_open_socket(js_interposer_t *interposer)
{
    // Open the existing Unix socket
    interposer->sockfd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (interposer->sockfd == -1)
    {
        interposer_log(LOG_ERROR, "Failed to create socket file descriptor when opening device: %s", interposer->open_dev_name);
        return -1;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(struct sockaddr_un));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, interposer->socket_path, sizeof(addr.sun_path) - 1);

    // Wait for socket to connect.
    int attempt = 0;
    while (attempt++ < SOCKET_CONNECT_TIMEOUT_MS)
    {
        if (connect(interposer->sockfd, (struct sockaddr *)&addr, sizeof(struct sockaddr_un)) == -1)
        {
            // sleep for 1ms
            usleep(1000);
            continue;
        }
        break;
    }
    if (attempt >= SOCKET_CONNECT_TIMEOUT_MS)
    {
        interposer_log(LOG_ERROR, "Failed to connect to socket at %s", interposer->socket_path);
        close(interposer->sockfd);
        return -1;
    }

    // Read the joystick config from the socket.
    if (read_config(interposer->sockfd, &(interposer->js_config)) != 0)
    {
        interposer_log(LOG_ERROR, "Failed to read config from socket: %s", interposer->socket_path);
        close(interposer->sockfd);
        return -1;
    }

    return 0;
}

// Interpose epoll_ctl to make joystck socket fd non-blocking.
int epoll_ctl(int epfd, int op, int fd, struct epoll_event *event)
{
    init_real_epoll_ctl();

    if (op == EPOLL_CTL_ADD)
    {
        // Find matching device in interposer list
        for (size_t i = 0; i < NUM_JS_INTERPOSERS; i++)
        {
            if (fd == interposers[i].sockfd)
            {
                interposer_log(LOG_INFO, "Socket %s (%d) was added to epoll (%d), set non-blocking", interposers[i].socket_path, fd, epfd);
                if (make_nonblocking(fd) == -1)
                {
                    interposer_log(LOG_ERROR, "Failed to make socket non-blocking");
                }
                break;
            }
        }
    }

    return real_epoll_ctl(epfd, op, fd, event);
}

// Interposer function for open syscall
int open(const char *pathname, int flags, ...)
{
    init_real_open();
    if (real_open == NULL)
    {
        interposer_log(LOG_ERROR, "Error getting original open function: %s", dlerror());
        return -1;
    }

    // Find matching device in interposer list
    js_interposer_t *interposer = NULL;
    for (size_t i = 0; i < NUM_JS_INTERPOSERS; i++)
    {
        if (strcmp(pathname, interposers[i].open_dev_name) == 0)
        {
            interposer = &interposers[i];
            break;
        }
    }

    // Call real open function if interposer was not found.
    if (interposer == NULL)
    {
        va_list args;
        va_start(args, flags);
        void *arg = va_arg(args, void *);
        va_end(args);
        return real_open(pathname, flags, arg);
    }

    if (interposer_open_socket(interposer) == -1)
        return -1;

    interposer_log(LOG_INFO, "Started interposer for 'open' call on %s with fd: %d", interposer->open_dev_name, interposer->sockfd);

    // Return the file descriptor of the unix socket.
    return interposer->sockfd;
}

// Interposer function for open64
int open64(const char *pathname, int flags, ...)
{
    init_real_open64();
    if (real_open64 == NULL)
    {
        interposer_log(LOG_ERROR, "Error getting original open64 function: %s", dlerror());
        return -1;
    }

    // Find matching device in interposer list
    js_interposer_t *interposer = NULL;
    for (size_t i = 0; i < NUM_JS_INTERPOSERS; i++)
    {
        if (strcmp(pathname, interposers[i].open_dev_name) == 0)
        {
            interposer = &interposers[i];
            break;
        }
    }

    // Call real open64
    if (interposer == NULL)
    {
        va_list args;
        va_start(args, flags);
        void *arg = va_arg(args, void *);
        va_end(args);
        return real_open64(pathname, flags, arg);
    }

    if (interposer_open_socket(interposer) == -1)
        return -1;

    interposer_log(LOG_INFO, "Started interposer for 'open64' call on %s with fd: %d", interposer->open_dev_name, interposer->sockfd);

    // Return the file descriptor of the unix socket.
    return interposer->sockfd;
}

// Interposer function for ioctl syscall on joystick device
int ioctl(int fd, unsigned long request, ...)
{
    init_real_ioctl();
    if (real_ioctl == NULL)
    {
        interposer_log(LOG_ERROR, "Error getting original ioctl function: %s", dlerror());
        return -1;
    }

    va_list args;
    va_start(args, request);

    // Get interposer for fd
    js_interposer_t *interposer = NULL;
    for (size_t i = 0; i < NUM_JS_INTERPOSERS; i++)
    {
        if (fd == interposers[i].sockfd)
        {
            interposer = &interposers[i];
            break;
        }
    }

    if (interposer == NULL)
    {
        // Not an ioctl on an interposed device, return real ioctl() call.
        void *arg = va_arg(args, void *);
        va_end(args);
        return real_ioctl(fd, request, arg);
    }

    if (((request >> 8) & 0xFF) != (('j')))
    {
        // Not a joystick type ioctl call, return real ioctl() call.
        void *arg = va_arg(args, void *);
        va_end(args);
        return real_ioctl(fd, request, arg);
    }

    // Handle the spoofed behavior for the character device
    // Cases are the second argument to the _IOR and _IOW macro call found in linux/joystick.h
    // The type of joystick ioctl is the first byte in the request.
    switch (request & 0xFF)
    {
    case 0x01: /* JSIOCGVERSION get driver version */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGVERSION(0x%08x) request for: %s", request, interposer->socket_path);
        uint32_t *version = va_arg(args, uint32_t *);
        *version = JS_VERSION;

        va_end(args);
        return 0; // 0 indicates success

    case 0x11: /* JSIOCGAXES get number of axes */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGAXES(0x%08x) request for: %s", request, interposer->socket_path);
        uint8_t *num_axes = va_arg(args, uint8_t *);
        *num_axes = interposer->js_config.num_axes;

        va_end(args);
        return 0; // 0 indicates success

    case 0x12: /* JSIOCGBUTTONS get number of buttons */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGBUTTONS(0x%08x) request for: %s", request, interposer->socket_path);
        uint8_t *btn_count = va_arg(args, uint8_t *);
        *btn_count = interposer->js_config.num_btns;

        va_end(args);
        return 0; // 0 indicates success

    case 0x13: /* JSIOCGNAME(len) get identifier string */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGNAME(0x%08x) request for: %s", request, interposer->socket_path);
        char *name = va_arg(args, char *);
        name[strlen(interposer->js_config.name)] = '\0';
        strncpy(name, interposer->js_config.name, strlen(interposer->js_config.name));
        va_end(args);
        return 0; // 0 indicates success

    case 0x21: /* JSIOCSCORR set correction values */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCSCORR(0x%08x) request for: %s", request, interposer->socket_path);
        va_end(args);
        return 0;

    case 0x22: /* JSIOCGCORR get correction values */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGCORR(0x%08x) request for: %s", request, interposer->socket_path);
        js_corr_t *corr = va_arg(args, js_corr_t *);
        memcpy(corr, &interposer->corr, sizeof(interposer->corr));

        va_end(args);
        return 0; // 0 indicates success

    case 0x31: /*  JSIOCSAXMAP set axis mapping */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCSAXMAP(0x%08x) request for: %s", request, interposer->socket_path);
        va_end(args);
        return 0; // 0 indicates success

    case 0x32: /* JSIOCGAXMAP get axis mapping */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGAXMAP(0x%08x) request for: %s", request, interposer->socket_path);
        uint8_t *axmap = va_arg(args, uint8_t *);
        memcpy(axmap, interposer->js_config.axes_map, interposer->js_config.num_axes * sizeof(uint8_t));
        va_end(args);
        return 0; // 0 indicates success

    case 0x33: /* JSIOCSBTNMAP set button mapping */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCSBTNMAP(0x%08x) request for: %s", request, interposer->socket_path);
        va_end(args);
        return 0; // 0 indicates success

    case 0x34: /* JSIOCGBTNMAP get button mapping */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGBTNMAP(0x%08x) request for: %s", request, interposer->socket_path);
        uint16_t *btn_map = va_arg(args, uint16_t *);
        memcpy(btn_map, interposer->js_config.btn_map, interposer->js_config.num_btns * sizeof(uint16_t));
        va_end(args);
        return 0; // 0 indicates success

    default:
        interposer_log(LOG_WARN, "Unhandled Intercepted ioctl request %lu", request, interposer->socket_path);
        void *arg = va_arg(args, void *);
        va_end(args);
        return real_ioctl(fd, request, arg);
    }

    // Handle other ioctl requests as needed
    return -ENOTTY; // Not a valid ioctl request for this character device emulation
}
