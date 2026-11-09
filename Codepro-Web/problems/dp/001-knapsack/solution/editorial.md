# Lời giải chi tiết: Bài toán cái túi

Gọi $dp[j]$ là giá trị lớn nhất có thể đạt được với sức chứa $j$.

Công thức chuyển trạng thái:
$$dp[j] = \max(dp[j], dp[j - w_i] + v_i)$$

Duyệt $j$ từ $W$ về $w_i$ để tránh việc dùng một món đồ nhiều lần.
Độ phức tạp thời gian: $O(N 	imes W)$.
Độ phức tạp không gian: $O(W)$.
