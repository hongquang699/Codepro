#pragma once
#include <sys/resource.h>

inline void apply_limits(rlim_t cpu_sec, rlim_t mem_bytes) {
    struct rlimit rl_cpu = {cpu_sec, cpu_sec + 1};
    setrlimit(RLIMIT_CPU, &rl_cpu);
    struct rlimit rl_as = {mem_bytes, mem_bytes};
    setrlimit(RLIMIT_AS, &rl_as);
}
