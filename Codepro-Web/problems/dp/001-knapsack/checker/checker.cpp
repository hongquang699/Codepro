#include "../../../judge/testlib/testlib.h"

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    long long ja = ans.readInt();
    long long pa = ouf.readInt();
    if (ja != pa) {
        quitf(_wa, "Wrong Answer: Expected %lld, found %lld", ja, pa);
    }
    quitf(_ok, "Accepted: Output is optimal");
}
