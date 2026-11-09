#include <iostream>
#include <string>
#include <chrono>
#include <thread>

int main(int argc, char* argv[]) {
    std::string worker_id = (argc > 1) ? argv[1] : "worker-default";
    std::cout << "[WORKER] Judge Worker started: " << worker_id << std::endl;
    while (true) {
        // Poll queue, execute sandbox, run checkers
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }
    return 0;
}
