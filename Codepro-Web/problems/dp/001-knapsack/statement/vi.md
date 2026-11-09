# Bài toán cái túi (0/1 Knapsack)

Một tên trộm đột nhập vào một cửa hàng có $N$ món đồ. Món đồ thứ $i$ có trọng lượng $w_i$ và giá trị $v_i$. Tên trộm mang theo một chiếc túi có sức chứa tối đa là $W$.

Hãy tìm giá trị tổng lớn nhất mà tên trộm có thể mang về mà không làm rách túi (tổng trọng lượng các món đồ được chọn không vượt quá $W$). Mỗi món đồ chỉ được chọn tối đa một lần.

## Dữ liệu vào
- Dòng đầu tiên chứa hai số nguyên $N$ và $W$ ($1 \le N \le 1000$, $1 \le W \le 10000$).
- $N$ dòng tiếp theo, dòng thứ $i$ chứa hai số nguyên $w_i$ và $v_i$ ($1 \le w_i \le W$, $1 \le v_i \le 10^6$).

## Dữ liệu ra
- In ra một số nguyên duy nhất là tổng giá trị lớn nhất thu được.

## Ví dụ
### Input
```
4 7
1 1
3 4
4 5
5 7
```

### Output
```
9
```

### Giải thích
Chọn đồ vật thứ 2 (nặng 3, giá trị 4) và đồ vật thứ 3 (nặng 4, giá trị 5). Tổng trọng lượng là $3 + 4 = 7 \le 7$, tổng giá trị là $4 + 5 = 9$.
