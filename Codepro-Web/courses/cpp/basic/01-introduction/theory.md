# Bài 1: Cấu trúc cơ bản của chương trình C++

## 1. Cú pháp cơ bản
Mỗi chương trình C++ bắt đầu từ hàm `main`:

```cpp
#include <iostream>

using namespace std;

int main() {
    cout << "Xin chao, The gioi!" << endl;
    return 0;
}
```

## 2. Các kiểu dữ liệu cơ sở
- `int`: Số nguyên 32-bit ($-2 	imes 10^9$ đến $2 	imes 10^9$).
- `long long`: Số nguyên 64-bit (khoảng $\pm 9 	imes 10^{18}$).
- `double`: Số thực độ chính xác kép.
- `bool`: Giá trị logic `true`/`false`.
- `string`: Chuỗi ký tự.
