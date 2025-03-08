#define _GNU_SOURCE
#include <dlfcn.h>
#include <dirent.h>
#include <errno.h>
// #include <fcntl.h>
#include <linux/inotify.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

// --- Fake file names for /dev/input ---
static const char *fake_entries[] = { "event1000", "event1001", NULL };
#define NUM_FAKE_ENTRIES 2

// --- Tracking open directory streams for /dev/input ---
struct fake_dir {
    DIR *dir;
    int index;  // next fake entry to return
};

#define MAX_FAKE_DIRS 1024
static struct fake_dir fake_dirs[MAX_FAKE_DIRS];
static int fake_dirs_count = 0;

// --- Tracking open fds for /dev/input (for getdents64) ---
struct fake_fd {
    int fd;
    int index;  // next fake entry to return
};

#define MAX_FAKE_FDS 1024
static struct fake_fd fake_fds[MAX_FAKE_FDS];
static int fake_fds_count = 0;

// --- Tracking inotify watches on /dev/input ---
struct fake_inotify_watch {
    int inotify_fd;         // inotify instance fd
    int watch_descriptor;   // the wd returned for /dev/input
    int events_delivered;   // flag: fake events already delivered?
};

#define MAX_FAKE_INOTIFY 1024
static struct fake_inotify_watch fake_inotify_watches[MAX_FAKE_INOTIFY];
static int fake_inotify_count = 0;

// --- Helper: check for /dev/input path ---
static int is_dev_input_path(const char *path) {
    return (path && strcmp(path, "/dev/input") == 0);
}

// --- opendir() wrapper ---
typedef DIR *(*orig_opendir_type)(const char *name);
static orig_opendir_type orig_opendir = NULL;

DIR *opendir(const char *name) {
    if (!orig_opendir)
        orig_opendir = dlsym(RTLD_NEXT, "opendir");
    DIR *dir = orig_opendir(name);
    if (dir && is_dev_input_path(name)) {
        printf("INTERPOSER: Saw opendir() on /dev/input path\n");
        // Record this DIR* so that readdir() returns fake entries.
        if (fake_dirs_count < MAX_FAKE_DIRS) {
            fake_dirs[fake_dirs_count].dir = dir;
            fake_dirs[fake_dirs_count].index = 0;
            fake_dirs_count++;
        }
    }
    return dir;
}

// --- closedir() wrapper ---
typedef int (*orig_closedir_type)(DIR *dir);
static orig_closedir_type orig_closedir = NULL;

int closedir(DIR *dir) {
    if (!orig_closedir)
        orig_closedir = dlsym(RTLD_NEXT, "closedir");
    // Remove any fake_dir record matching this DIR*
    for (int i = 0; i < fake_dirs_count; i++) {
        if (fake_dirs[i].dir == dir) {
            fake_dirs[i] = fake_dirs[fake_dirs_count - 1];
            fake_dirs_count--;
            break;
        }
    }
    return orig_closedir(dir);
}

// --- readdir() wrapper ---
typedef struct dirent *(*orig_readdir_type)(DIR *dirp);
static orig_readdir_type orig_readdir = NULL;

struct dirent *readdir(DIR *dirp) {
    // Check if this DIR* is one of our fake /dev/input directories.
    for (int i = 0; i < fake_dirs_count; i++) {
        if (fake_dirs[i].dir == dirp) {
            printf("INTERPOSER: Saw readdir() on /dev/input path\n");
            if (fake_dirs[i].index < NUM_FAKE_ENTRIES) {
                // Prepare a fake dirent. (Note: readdir() is not thread‐safe.)
                static struct dirent fake_de;
                memset(&fake_de, 0, sizeof(fake_de));
                const char *name = fake_entries[fake_dirs[i].index];
                strncpy(fake_de.d_name, name, sizeof(fake_de.d_name) - 1);
                fake_dirs[i].index++;
                return &fake_de;
            } else {
                return NULL;  // end of directory
            }
        }
    }
    if (!orig_readdir)
        orig_readdir = dlsym(RTLD_NEXT, "readdir");
    return orig_readdir(dirp);
}

// --- getdents64() wrapper ---
// (Used by some applications instead of readdir.)
struct linux_dirent64 {
    ino64_t d_ino;
    off64_t d_off;
    unsigned short d_reclen;
    unsigned char d_type;
    char d_name[];
};

typedef ssize_t (*orig_getdents64_type)(int fd, struct linux_dirent64 *dirp, size_t count);
static orig_getdents64_type orig_getdents64 = NULL;

ssize_t getdents64(int fd, void *__buffer, size_t count) {
    struct linux_dirent64 *dirp = __buffer;
    // Check if this fd was opened on /dev/input.
    for (int i = 0; i < fake_fds_count; i++) {
        if (fake_fds[i].fd == fd) {
            char *buf = (char *)dirp;
            size_t bytes_written = 0;
            int index = fake_fds[i].index;
            while (index < NUM_FAKE_ENTRIES) {
                const char *name = fake_entries[index];
                int namelen = strlen(name);
                size_t reclen = offsetof(struct linux_dirent64, d_name) + namelen + 1;
                // Align to 8 bytes.
                if (reclen % 8 != 0)
                    reclen += 8 - (reclen % 8);
                if (bytes_written + reclen > count)
                    break;
                struct linux_dirent64 *d = (struct linux_dirent64 *)(buf + bytes_written);
                d->d_ino = 0;
                d->d_off = 0;
                d->d_reclen = reclen;
                d->d_type = DT_UNKNOWN;
                strncpy(d->d_name, name, namelen + 1);
                bytes_written += reclen;
                index++;
            }
            fake_fds[i].index = index;
            return bytes_written;
        }
    }
    if (!orig_getdents64)
        orig_getdents64 = dlsym(RTLD_NEXT, "getdents64");
    return orig_getdents64(fd, dirp, count);
}

// --- open() wrapper ---
// We intercept open() to catch an attempt to open /dev/input as a directory.
typedef int (*orig_open_type)(const char *pathname, int flags, ...);
static orig_open_type orig_open = NULL;

int open(const char *pathname, int flags, ...) {
    if (!orig_open)
        orig_open = dlsym(RTLD_NEXT, "open");
    int fd;
    va_list args;
    va_start(args, flags);
    if (flags & O_CREAT) {
        mode_t mode = va_arg(args, mode_t);
        fd = orig_open(pathname, flags, mode);
    } else {
        fd = orig_open(pathname, flags);
    }
    va_end(args);
    if (fd >= 0 && is_dev_input_path(pathname)) {
        if (fake_fds_count < MAX_FAKE_FDS) {
            fake_fds[fake_fds_count].fd = fd;
            fake_fds[fake_fds_count].index = 0;
            fake_fds_count++;
        }
    }
    return fd;
}

// --- close() wrapper ---
// We also use close() to remove tracked fds (for both directory and inotify fds).
typedef int (*orig_close_type)(int fd);
static orig_close_type orig_close = NULL;

int close(int fd) {
    if (!orig_close)
        orig_close = dlsym(RTLD_NEXT, "close");
    // Remove fake_fd if it exists.
    for (int i = 0; i < fake_fds_count; i++) {
        if (fake_fds[i].fd == fd) {
            fake_fds[i] = fake_fds[fake_fds_count - 1];
            fake_fds_count--;
            break;
        }
    }
    // Remove inotify mapping if present.
    for (int i = 0; i < fake_inotify_count; i++) {
        if (fake_inotify_watches[i].inotify_fd == fd) {
            fake_inotify_watches[i] = fake_inotify_watches[fake_inotify_count - 1];
            fake_inotify_count--;
            break;
        }
    }
    return orig_close(fd);
}

// --- inotify_add_watch() wrapper ---
// When an application adds a watch on "/dev/input", we record the watch so that later
// we can return fake events.
typedef int (*orig_inotify_add_watch_type)(int fd, const char *pathname, uint32_t mask);
static orig_inotify_add_watch_type orig_inotify_add_watch = NULL;

int inotify_add_watch(int fd, const char *pathname, uint32_t mask) {
    if (!orig_inotify_add_watch)
        orig_inotify_add_watch = dlsym(RTLD_NEXT, "inotify_add_watch");
    int wd = orig_inotify_add_watch(fd, pathname, mask);
    if (wd >= 0 && is_dev_input_path(pathname)) {
        if (fake_inotify_count < MAX_FAKE_INOTIFY) {
            fake_inotify_watches[fake_inotify_count].inotify_fd = fd;
            fake_inotify_watches[fake_inotify_count].watch_descriptor = wd;
            fake_inotify_watches[fake_inotify_count].events_delivered = 0;
            fake_inotify_count++;
        }
    }
    return wd;
}

// --- read() wrapper ---
// Intercepts read() on inotify file descriptors and, for our fake watches,
// returns fake events that simulate the appearance of our fake files.
typedef ssize_t (*orig_read_type)(int fd, void *buf, size_t count);
static orig_read_type orig_read = NULL;

ssize_t read(int fd, void *buf, size_t count) {
    if (!orig_read)
        orig_read = dlsym(RTLD_NEXT, "read");
    // Check if this fd is an inotify fd with a watch on /dev/input.
    for (int i = 0; i < fake_inotify_count; i++) {
        if (fake_inotify_watches[i].inotify_fd == fd && fake_inotify_watches[i].events_delivered == 0) {
            char *buffer = buf;
            size_t bytes_written = 0;
            // Create one event per fake file.
            for (int j = 0; j < NUM_FAKE_ENTRIES; j++) {
                const char *name = fake_entries[j];
                int namelen = strlen(name);
                size_t event_size = sizeof(struct inotify_event) + namelen + 1;
                if (bytes_written + event_size > count)
                    break;
                struct inotify_event *event = (struct inotify_event *)(buffer + bytes_written);
                event->wd = fake_inotify_watches[i].watch_descriptor;
                event->mask = IN_CREATE;  // Simulate a file creation event.
                event->cookie = 0;
                event->len = namelen + 1;
                strncpy(event->name, name, namelen + 1);
                bytes_written += event_size;
            }
            fake_inotify_watches[i].events_delivered = 1;  // Only deliver once.
            return bytes_written;
        }
    }
    return orig_read(fd, buf, count);
}
