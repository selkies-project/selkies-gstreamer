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

    Note that some applications list the /dev/input/ directory to discover JS devices, to solve for this, create empty files at the following paths:
        sudo mkdir -pm1777 /dev/input
        sudo touch /dev/input/{js0,js1,js2,js3,event1000,event1001,event1002,event1003}
        sudo chmod 777 /dev/input/js* /dev/input/event*
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

// Raw joystick interposer constants.
#define JS0_DEVICE_PATH "/dev/input/js0"
#define JS0_SOCKET_PATH "/tmp/selkies_js0.sock"
#define JS1_DEVICE_PATH "/dev/input/js1"
#define JS1_SOCKET_PATH "/tmp/selkies_js1.sock"
#define JS2_DEVICE_PATH "/dev/input/js2"
#define JS2_SOCKET_PATH "/tmp/selkies_js2.sock"
#define JS3_DEVICE_PATH "/dev/input/js3"
#define JS3_SOCKET_PATH "/tmp/selkies_js3.sock"
#define NUM_JS_INTERPOSERS 4

// Event type joystick interposer constant.
#define EV0_DEVICE_PATH "/dev/input/event1000"
#define EV0_SOCKET_PATH "/tmp/selkies_event1000.sock"
#define EV1_DEVICE_PATH "/dev/input/event1001"
#define EV1_SOCKET_PATH "/tmp/selkies_event1001.sock"
#define EV2_DEVICE_PATH "/dev/input/event1002"
#define EV2_SOCKET_PATH "/tmp/selkies_event1002.sock"
#define EV3_DEVICE_PATH "/dev/input/event1003"
#define EV3_SOCKET_PATH "/tmp/selkies_event1003.sock"
#define NUM_EV_INTERPOSERS 4

// Macros for working with interposer count and indexing.
#define NUM_INTERPOSERS() NUM_JS_INTERPOSERS + NUM_EV_INTERPOSERS

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

// Function that takes the address of a function pointer and uses dlsym to load the system function into it
static int load_real_func(void (**target)(void), const char *name)
{
    if (*target != NULL)
        return 0;
    *target = dlsym(RTLD_NEXT, name);
    if (target == NULL)
    {
        interposer_log(LOG_ERROR, "Error getting original '%s' function: %s", name, dlerror());
        return -1;
    }
    return 0;
}

// Function pointers to original calls
static int (*real_open)(const char *pathname, int flags, ...) = NULL;
static int (*real_open64)(const char *pathname, int flags, ...) = NULL;
static int (*real_ioctl)(int fd, unsigned long request, ...) = NULL;
static int (*real_epoll_ctl)(int epfd, int op, int fd, struct epoll_event *event) = NULL;
static int (*real_close)(int fd) = NULL;

// Initialization function to load the real functions
__attribute__((constructor)) void init_interposer()
{
    load_real_func((void *)&real_open, "open");
    load_real_func((void *)&real_open64, "open64");
    load_real_func((void *)&real_ioctl, "ioctl");
    load_real_func((void *)&real_epoll_ctl, "epoll_ctl");
    load_real_func((void *)&real_close, "close");
}

// Type definition for correction struct
typedef struct js_corr js_corr_t;

typedef struct
{
    char name[255];        // Name of the controller
    uint16_t vendor;       // Vendor ID
    uint16_t product;      // Product ID
    uint16_t version;      // Version number
    uint16_t num_btns;     // Number of buttons
    uint16_t num_axes;     // Number of axes
    uint16_t btn_map[512]; // Button map
    uint8_t axes_map[64];  // axes map
} js_config_t;

// Struct for storing information about each interposed joystick device.
typedef struct
{
    uint8_t type;
    char open_dev_name[255];
    char socket_path[255];
    int sockfd;
    js_corr_t corr;
    js_config_t js_config;
} js_interposer_t;

#define DEV_TYPE_JS 0
#define DEV_TYPE_EV 1

// Min/max values for ABS axes
#define ABS_AXIS_MIN -32767
#define ABS_AXIS_MAX 32767
#define ABS_HAT_MIN -1
#define ABS_HAT_MAX 1

static js_interposer_t interposers[NUM_INTERPOSERS()] = {
    {
        type : DEV_TYPE_JS,
        open_dev_name : JS0_DEVICE_PATH,
        socket_path : JS0_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
    {
        type : DEV_TYPE_JS,
        open_dev_name : JS1_DEVICE_PATH,
        socket_path : JS1_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
    {
        type : DEV_TYPE_JS,
        open_dev_name : JS2_DEVICE_PATH,
        socket_path : JS2_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
    {
        type : DEV_TYPE_JS,
        open_dev_name : JS3_DEVICE_PATH,
        socket_path : JS3_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
    {
        type : DEV_TYPE_EV,
        open_dev_name : EV0_DEVICE_PATH,
        socket_path : EV0_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
    {
        type : DEV_TYPE_EV,
        open_dev_name : EV1_DEVICE_PATH,
        socket_path : EV1_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
    {
        type : DEV_TYPE_EV,
        open_dev_name : EV2_DEVICE_PATH,
        socket_path : EV2_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
    {
        type : DEV_TYPE_EV,
        open_dev_name : EV3_DEVICE_PATH,
        socket_path : EV3_SOCKET_PATH,
        sockfd : -1,
        corr : {},
        js_config : {},
    },
};

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

    // Send architecture word length to tell client to send 64 vs 32bit wide messages.
    unsigned char arch[1] = {sizeof(unsigned long)};
    write(interposer->sockfd, arch, sizeof(arch));

    return 0;
}

// Interpose epoll_ctl to make joystck socket fd non-blocking.
int epoll_ctl(int epfd, int op, int fd, struct epoll_event *event)
{
    if (load_real_func((void *)&real_epoll_ctl, "epoll_ctl") < 0)
        return -1;
    if (op == EPOLL_CTL_ADD)
    {
        // Find matching device in interposer list
        for (size_t i = 0; i < NUM_INTERPOSERS(); i++)
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
    if (load_real_func((void *)&real_open, "open") < 0)
        return -1;

    // Find matching device in interposer list
    js_interposer_t *interposer = NULL;
    for (size_t i = 0; i < NUM_INTERPOSERS(); i++)
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

    make_nonblocking(interposer->sockfd);
    interposer_log(LOG_INFO, "Started interposer for 'open' call on %s with fd: %d", interposer->open_dev_name, interposer->sockfd);

    // Return the file descriptor of the unix socket.
    return interposer->sockfd;
}

// Interposer function for open64
int open64(const char *pathname, int flags, ...)
{
    if (load_real_func((void *)&real_open64, "open64") < 0)
        return -1;
    // Find matching device in interposer list
    js_interposer_t *interposer = NULL;
    for (size_t i = 0; i < NUM_INTERPOSERS(); i++)
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

// Interposer function for close
int close(int fd)
{
    if (load_real_func((void *)&real_close, "close") < 0)
        return -1;
    // Get interposer for fd
    js_interposer_t *interposer = NULL;
    for (size_t i = 0; i < NUM_INTERPOSERS(); i++)
    {
        if (fd >= 0 && fd == interposers[i].sockfd)
        {
            interposer = &interposers[i];
            break;
        }
    }

    // Clear the interposer.
    if (interposer != NULL)
    {
        interposer_log(LOG_INFO, "Saw 'close' for socket %s with fd: %d, stopping interposer", interposer->socket_path, interposer->sockfd);
        interposer->sockfd = -1;
    }

    return real_close(fd);
}

// Handler for joystick type ioctl calls
int intercept_js_ioctl(js_interposer_t *interposer, int fd, unsigned long request, ...)
{
    va_list args;
    va_start(args, request);
    void *arg = va_arg(args, void *);
    va_end(args);

    int len;

    // Handle the spoofed behavior for the character device
    // Cases are the second argument to the _IOR and _IOW macro call found in linux/joystick.h
    // The type of joystick ioctl is the first byte in the request.
    switch (_IOC_NR(request))
    {
    case 0x01: /* JSIOCGVERSION get driver version */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGVERSION(0x%08x) request for: %s", request, interposer->socket_path);
        uint32_t *version = (uint32_t *)arg;
        *version = JS_VERSION;
        return 0;

    case 0x11: /* JSIOCGAXES get number of axes */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGAXES(0x%08x) request for: %s", request, interposer->socket_path);
        uint8_t *num_axes = (uint8_t *)arg;
        *num_axes = interposer->js_config.num_axes;
        return 0;

    case 0x12: /* JSIOCGBUTTONS get number of buttons */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGBUTTONS(0x%08x) request for: %s", request, interposer->socket_path);
        uint8_t *btn_count = (uint8_t *)arg;
        *btn_count = interposer->js_config.num_btns;
        return 0;

    case 0x13: /* JSIOCGNAME(len) get identifier string */
        len = _IOC_SIZE(request);
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGNAME(%d)(0x%08x) request for: %s", len, request, interposer->socket_path);
        strcpy(arg, interposer->js_config.name);
        // the JSIO ioctls always return 0;
        return 0;

    case 0x21: /* JSIOCSCORR set correction values */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCSCORR(0x%08x) request for: %s", request, interposer->socket_path);
        return 0;

    case 0x22: /* JSIOCGCORR get correction values */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGCORR(0x%08x) request for: %s", request, interposer->socket_path);
        js_corr_t *corr = (js_corr_t *)arg;
        memcpy(corr, &interposer->corr, sizeof(interposer->corr));

        return 0;

    case 0x31: /*  JSIOCSAXMAP set axis mapping */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCSAXMAP(0x%08x) request for: %s", request, interposer->socket_path);
        return 0;

    case 0x32: /* JSIOCGAXMAP get axis mapping */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGAXMAP(0x%08x) request for: %s", request, interposer->socket_path);
        uint8_t *axmap = (uint8_t *)arg;
        memcpy(axmap, interposer->js_config.axes_map, interposer->js_config.num_axes * sizeof(uint8_t));
        return 0;

    case 0x33: /* JSIOCSBTNMAP set button mapping */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCSBTNMAP(0x%08x) request for: %s", request, interposer->socket_path);
        return 0;

    case 0x34: /* JSIOCGBTNMAP get button mapping */
        interposer_log(LOG_INFO, "Intercepted ioctl JSIOCGBTNMAP(0x%08x) request for: %s", request, interposer->socket_path);
        uint16_t *btn_map = (uint16_t *)arg;
        memcpy(btn_map, interposer->js_config.btn_map, interposer->js_config.num_btns * sizeof(uint16_t));
        return 0;

    default:
        interposer_log(LOG_WARN, "Unhandled 'joystick' ioctl intercept request 0x%08x", request, interposer->socket_path);
        return real_ioctl(fd, request, arg);
    }

    // Not a valid ioctl request for this character device emulation
    return -ENOTTY;
}

// Handler for event type ioctl calls
int intercept_ev_ioctl(js_interposer_t *interposer, int fd, unsigned long request, ...)
{
    va_list args;
    va_start(args, request);
    void *arg = va_arg(args, void *);
    va_end(args);

    struct input_absinfo *absinfo;
    struct input_id *id;
    int fake_version = 0x010100;
    int len;

    /* The EVIOCGABS(key) is a request to get the calibration values for the ABS type axes.
     * Each axes returned by the ioctl EVIOCGBIT(EV_ABS) request is evaluated.
     * since there is no need to emulate calibration values, the target value is zero.
     */
    if ((request >= EVIOCGABS(ABS_X) && request <= EVIOCGABS(ABS_MAX)))
    {
        // The actual ABS axis is offset by the ioctl request, 0x40.
        // https://github.com/libsdl-org/SDL/blob/cf249b0cb28336d14bbd6cb0bd4f711f6ad4db87/src/joystick/linux/SDL_sysjoystick.c#L1237
        uint8_t abs = (request & 0xFF) - 0x40;
        absinfo = (struct input_absinfo *)arg;
        absinfo->value = 0;
        if (request == EVIOCGABS(ABS_RZ) || request == EVIOCGABS(ABS_Z))
        {
            absinfo->minimum = 0;
            absinfo->maximum = 255;
        }
        else if (request <= EVIOCGABS(ABS_BRAKE))
        {
            absinfo->minimum = ABS_AXIS_MIN;
            absinfo->maximum = ABS_AXIS_MAX;
            absinfo->fuzz = 16;
            absinfo->flat = 128;
        }
        else if (request >= EVIOCGABS(ABS_HAT0X) && request <= EVIOCGABS(ABS_HAT3Y))
        {
            absinfo->minimum = ABS_HAT_MIN;
            absinfo->maximum = ABS_HAT_MAX;
        }

        interposer_log(LOG_INFO, "Matched ioctl EVIOCGABS(0x%x)(0x%08x), request for %s", abs, request, interposer->socket_path);
        return 1;
    }

    switch (_IOC_NR(request))
    {
    case (0x20 + EV_SYN): /* Handle EVIOCGBIT for EV_SYN: sync event */
        len = _IOC_SIZE(request);
        memset(arg, 0, len);
        unsigned long evbits[3] = {EV_SYN, EV_KEY, EV_ABS};
        int index = 0;
        for (size_t i = 0; i < sizeof(evbits) / sizeof(unsigned long); i++)
        {
            index = evbits[i] / 8;
            ((unsigned char *)arg)[index] |= (1 << (evbits[i] % 8));
        }
        interposer_log(LOG_INFO, "Intercepted ioctl EVIOCGBIT(EV_SYN, %d)(0x%x), request for %s", len, request, interposer->socket_path);
        return 0;

    case (0x20 + EV_ABS): /* Handle EVIOCGBIT for EV_ABS: report supported axes. */
        len = _IOC_SIZE(request);
        memset(arg, 0, len);
        // set the bit corresponding to each supported axis.
        for (size_t i = 0; i < interposer->js_config.num_axes; i++)
        {
            int bit = interposer->js_config.axes_map[i];
            int index = bit / 8;
            if (index < len)
            {
                ((unsigned char *)arg)[index] |= (1 << (bit % 8));
            }
        }
        interposer_log(LOG_INFO, "Intercepted ioctl EVIOCGBIT(EV_ABS, %d)(0x%x), request for %s", len, request, interposer->socket_path);

        return interposer->js_config.num_axes;

    case (0x20 + EV_REL): /* Handle EVIOCGBIT for EV_REL: report supported relative events. */
        len = _IOC_SIZE(request);
        memset(arg, 0, len);
        interposer_log(LOG_INFO, "Intercepted ioctl EVIOCGBIT(EV_REL, %d)(0x%x), request for %s", len, request, interposer->socket_path);
        return 0;

    case (0x20 + EV_KEY): /* Handle EVIOCGBIT for EV_KEY: report supported keys. */
        len = _IOC_SIZE(request);
        memset(arg, 0, len);
        // set the bit corresponding to each supported key.
        for (size_t i = 0; i < interposer->js_config.num_btns; i++)
        {
            int bit = interposer->js_config.btn_map[i];
            int index = bit / 8;
            if (index < len)
            {
                ((unsigned char *)arg)[index] |= (1 << (bit % 8));
            }
        }
        interposer_log(LOG_INFO, "Intercepted ioctl EVIOCGBIT(EV_KEY, %d)(0x%x), request for %s", len, request, interposer->socket_path);
        return interposer->js_config.num_btns;

    case (0x20 + EV_FF): /* Handle EVIOCGBIT for EV_FF: report supported force feedback. */
        // TODO: Support force feedback
        len = _IOC_SIZE(request);
        memset(arg, 0, len);
        interposer_log(LOG_INFO, "Intercepted ioctl EVIOCGBIT(EV_FF, %d)(0x%x), request for %s", len, request, interposer->socket_path);
        return -1;
    
    case 0x81: /* Handle EVIOCRMFF: Erase a force effect */
        // TODO: Support force feedback
        interposer_log(LOG_INFO, "Intercepted ioctl EVIOCRMFF()(0x%x), request for %s", request, interposer->socket_path);
        return 0;

    case 0x06: /* Handle EVIOCGNAME: Get device name. */
        len = _IOC_SIZE(request);
        strcpy(arg, interposer->js_config.name);
        interposer_log(LOG_INFO, "Intercepted ioctl EVIOCGNAME(%d)(0x%08x) for %s", len, request, interposer->socket_path);
        return strlen(interposer->js_config.name);

    case 0x01: /* Handle EVIOCGVERSION: device version request. */
        memcpy(arg, &fake_version, sizeof(fake_version));
        interposer_log(LOG_INFO, "Intercepted ioctl EVIOCGVERSION(0x%08x) for %s", request, interposer->socket_path);
        return 0;

    case 0x02: /* Handle EVIOCGID: device ID request. */
        memset(arg, 0, sizeof(struct input_id));
        id = (struct input_id *)arg;
        // Populate the fake input_id for a joystick device
        id->bustype = BUS_VIRTUAL;                   // Example bus type (Virtual)
        id->vendor = interposer->js_config.vendor;   // Fake vendor ID (Microsoft)
        id->product = interposer->js_config.product; // Fake product ID (Xbox360 Wired Controller)
        id->version = interposer->js_config.version; // Fake version
        interposer_log(LOG_INFO, "Intercepted ioctl EVIOCGID(0x%08x), bustype = %d, vendor = 0x%.4x, product = 0x%.4x, version = %d, for %s", request, id->bustype, id->vendor, id->product, id->version, interposer->socket_path);
        return 0;

    case 0x09: /* Handle EVIOCGPROP(len): report device properties */
        len = _IOC_SIZE(request);
        memset(arg, 0, len);
        interposer_log(LOG_INFO, "Intercepted ioctl EVIOCGPROP(%d)(0x%x), request for %s", len, request, interposer->socket_path);
        return 0;

    case 0x18: /* Handle EVIOCGKEY(len): report state of all buttons */
        len = _IOC_SIZE(request);
        memset(arg, 0, len);
        interposer_log(LOG_INFO, "Intercepted ioctl EVIOCGKEY(%d)(0x%x), request for %s", len, request, interposer->socket_path);
        return interposer->js_config.num_btns;

    case 0x90: /* Handle EVIOCGRAB: grab device for exclusive access */
        interposer_log(LOG_INFO, "Matched ioctl EVIOCGRAB(0x%08x), request for %s", request, interposer->socket_path);
        return 0;

    case 0x07: /* Handle EVIOCGPHYS: Get physical location. */
        len = _IOC_SIZE(request);
        interposer_log(LOG_INFO, "Matched ioctl EVIOCGPHYS(%d)(0x%08x) for %s", len, request, interposer->socket_path);
        return 0;

    case 0x08: /* Handle EVIOCGUNIQ: Get device name. */
        len = _IOC_SIZE(request);
        interposer_log(LOG_INFO, "Matched ioctl EVIOCGUNIQ(%d)(0x%08x) for %s", len, request, interposer->socket_path);
        return -1;

    default:
        interposer_log(LOG_WARN, "Unhandled EV ioctl request (0x%08x) for %s", request, interposer->socket_path);
        return 0;
    }
}

// Interposer function for ioctl syscall
int ioctl(int fd, unsigned long request, ...)
{
    if (load_real_func((void *)&real_ioctl, "ioctl") < 0)
        return -1;
    va_list args;
    va_start(args, request);
    void *arg = va_arg(args, void *);
    va_end(args);

    // Get interposer for fd
    js_interposer_t *interposer = NULL;
    for (size_t i = 0; i < NUM_INTERPOSERS(); i++)
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
        return real_ioctl(fd, request, arg);
    }
    else if ((_IOC_TYPE(request) == 'j'))
    {
        return intercept_js_ioctl(interposer, fd, request, arg);
    }
    else if ((_IOC_TYPE(request) == 'E'))
    {
        return intercept_ev_ioctl(interposer, fd, request, arg);
    }
    else
    {
        interposer_log(LOG_WARN, "No ioctl interceptor for request 0x%08x on %s", request, interposer->socket_path);
        return real_ioctl(fd, request, arg);
    }
}
