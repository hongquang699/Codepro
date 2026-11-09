#include <stdio.h>

void setup_seccomp_filter() {
    // Whitelist only safe syscalls: read, write, exit, brk, mmap, fstat
}
