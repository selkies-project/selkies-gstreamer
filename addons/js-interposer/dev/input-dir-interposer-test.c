#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <errno.h>
#include <string.h>

int main(void) {
    const char *dir_path = "/dev/input";
    DIR *dir = opendir(dir_path);
    if (!dir) {
        perror("opendir");
        return EXIT_FAILURE;
    }
    printf("Listing directory: %s\n", dir_path);
    struct dirent *entry;
    while ((entry = readdir(dir)) != NULL) {
        printf("Found entry: %s\n", entry->d_name);
    }
    closedir(dir);
    return EXIT_SUCCESS;
}