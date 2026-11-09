// Custom testlib checker template
#include "../../testlib/testlib.h"

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    int user_ans = ouf.readInt();
    int jury_ans = ans.readInt();
    if (user_ans == jury_ans) {
        quitf(_ok, "Correct answer!");
    } else {
        quitf(_wa, "Expected %d, found %d", jury_ans, user_ans);
    }
}
