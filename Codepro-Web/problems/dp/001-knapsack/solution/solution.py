import sys

def main():
    input = sys.stdin.read
    data = input().split()
    if not data:
        return
    n = int(data[0])
    W = int(data[1])

    dp = [0] * (W + 1)
    idx = 2
    for _ in range(n):
        w = int(data[idx])
        v = int(data[idx + 1])
        idx += 2
        for j in range(W, w - 1, -1):
            if dp[j - w] + v > dp[j]:
                dp[j] = dp[j - w] + v

    print(dp[W])

if __name__ == '__main__':
    main()
