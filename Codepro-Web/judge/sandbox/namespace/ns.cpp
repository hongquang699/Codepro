#define _GNU_SOURCE
#include <sched.h>
#include <unistd.h>

int isolate_namespaces() {
    return unshare(CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWIPC | CLONE_NEWNS);
}
