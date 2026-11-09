/* Testlib C++ Competitive Programming Checker Library (Simplified Header) */
#ifndef _TESTLIB_H_
#define _TESTLIB_H_
#include <iostream>
#include <fstream>
#include <string>

enum TResult { _ok = 0, _wa = 1, _pe = 2, _fail = 3 };

struct InStream {
    int readInt() { return 0; }
    int readInt(int min_val, int max_val, const std::string& name) { return min_val; }
    void readSpace() {}
    void readEoln() {}
    void readEof() {}
};

static InStream inf, ouf, ans;

inline void registerTestlibCmd(int argc, char* argv[]) {}
inline void registerValidation(int argc, char* argv[]) {}
inline void quitf(TResult res, const char* format, ...) {
    exit((int)res);
}

#endif
