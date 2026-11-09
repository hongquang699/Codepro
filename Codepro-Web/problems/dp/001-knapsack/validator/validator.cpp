#include "../../../judge/testlib/testlib.h"

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);
    int n = inf.readInt(1, 1000, "N");
    inf.readSpace();
    int W = inf.readInt(1, 10000, "W");
    inf.readEoln();
    for (int i = 0; i < n; ++i) {
        inf.readInt(1, W, "w_i");
        inf.readSpace();
        inf.readInt(1, 1000000, "v_i");
        inf.readEoln();
    }
    inf.readEof();
    return 0;
}
