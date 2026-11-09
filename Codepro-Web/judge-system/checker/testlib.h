/* 
 * testlib.h - Testlib Compatibility Header for Judge System
 * Compatible with standard competitive programming custom checkers and validators.
 */
#ifndef _TESTLIB_H_
#define _TESTLIB_H_

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cstdlib>
#include <cstdarg>
#include <cmath>

enum TResult {
    _ok = 0,
    _wa = 1,
    _pe = 2,
    _fail = 3,
    _dirt = 4,
    _points = 5,
    _unexpected_eof = 8
};

struct InStream {
    std::ifstream file;
    std::string name;

    void init(const std::string& filename, const std::string& streamName) {
        name = streamName;
        file.open(filename);
    }

    std::string readToken() {
        std::string s;
        if (!(file >> s)) return "";
        return s;
    }

    std::string readString() {
        std::string s;
        if (!std::getline(file, s)) return "";
        return s;
    }

    long long readLong() {
        long long v = 0;
        file >> v;
        return v;
    }

    int readInt() {
        int v = 0;
        file >> v;
        return v;
    }

    int readInt(int min_val, int max_val, const std::string& var_name = "") {
        int v = readInt();
        if (v < min_val || v > max_val) {
            std::cerr << "FAIL: Variable " << var_name << " value " << v 
                      << " out of bounds [" << min_val << ", " << max_val << "]\n";
            exit(_fail);
        }
        return v;
    }

    double readDouble() {
        double v = 0.0;
        file >> v;
        return v;
    }

    bool seekEof() {
        std::string dummy;
        return !(file >> dummy);
    }

    void readSpace() {}
    void readEoln() {}
    void readEof() {}
};

static InStream inf, ouf, ans;

inline void quitf(TResult res, const char* format, ...) {
    va_list args;
    va_start(args, format);
    char buffer[1024];
    vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);

    if (res == _ok) {
        std::cout << "OK: " << buffer << "\n";
        exit(0);
    } else if (res == _wa) {
        std::cerr << "WA: " << buffer << "\n";
        exit(1);
    } else if (res == _pe) {
        std::cerr << "PE: " << buffer << "\n";
        exit(2);
    } else {
        std::cerr << "FAIL: " << buffer << "\n";
        exit(3);
    }
}

inline void registerTestlibCmd(int argc, char* argv[]) {
    if (argc >= 4) {
        inf.init(argv[1], "input");
        ouf.init(argv[2], "output");
        ans.init(argv[3], "answer");
    }
}

inline void registerValidation(int argc, char* argv[]) {
    if (argc >= 2) {
        inf.init(argv[1], "input");
    }
}

#endif // _TESTLIB_H_
