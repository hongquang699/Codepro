#include "../testlib/testlib.h"

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);
    int n = inf.readInt(1, 1000, "n");
    inf.readSpace();
    int w = inf.readInt(1, 10000, "W");
    inf.readEoln();
    inf.readEof();
    return 0;
}
