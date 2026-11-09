// Token by token comparison checker
#include <iostream>
#include <fstream>
#include <string>

int main(int argc, char* argv[]) {
    if (argc < 4) return 3; // FAIL
    std::ifstream user_out(argv[2]);
    std::ifstream answer(argv[3]);
    std::string token1, token2;
    while (answer >> token1) {
        if (!(user_out >> token2)) return 1; // WA
        if (token1 != token2) return 1; // WA
    }
    if (user_out >> token2) return 1; // WA: Extra tokens
    return 0; // AC
}
