#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int n, W;
    if (!(cin >> n >> W)) return 0;

    vector<long long> dp(W + 1, 0);

    for (int i = 0; i < n; ++i) {
        int w;
        long long v;
        cin >> w >> v;
        for (int j = W; j >= w; --j) {
            dp[j] = max(dp[j], dp[j - w] + v);
        }
    }

    cout << dp[W] << "\n";
    return 0;
}
