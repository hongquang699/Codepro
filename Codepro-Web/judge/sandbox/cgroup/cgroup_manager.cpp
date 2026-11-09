#include <fstream>
#include <string>

void create_cgroup(const std::string& cg_name, long memory_bytes) {
    std::ofstream mem_max("/sys/fs/cgroup/" + cg_name + "/memory.max");
    if (mem_max.is_open()) {
        mem_max << memory_bytes;
    }
}
