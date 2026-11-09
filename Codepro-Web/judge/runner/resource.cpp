#if defined(_WIN32)
#include <windows.h>
#else
#include <sys/resource.h>
#endif

void set_process_limits(int time_limit_sec, int memory_limit_mb) {
#if defined(_WIN32)
    (void)time_limit_sec;
    (void)memory_limit_mb;
#else
    struct rlimit r_time;
    r_time.rlim_cur = time_limit_sec;
    r_time.rlim_max = time_limit_sec + 1;
    setrlimit(RLIMIT_CPU, &r_time);

    struct rlimit r_mem;
    r_mem.rlim_cur = static_cast<rlim_t>(memory_limit_mb) * 1024 * 1024;
    r_mem.rlim_max = static_cast<rlim_t>(memory_limit_mb) * 1024 * 1024;
    setrlimit(RLIMIT_AS, &r_mem);
#endif
}
