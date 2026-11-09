/**
 * CodeProOJ - User Enrolled Courses Controller
 */
const UserCourses = {
  getMyCourses() {
    return [
      { id: 'cpp', name: 'Nhập Môn Lập Trình C++', progress: 75 },
      { id: 'dsa', name: 'Cấu Trúc Dữ Liệu & Thuật Toán', progress: 40 }
    ];
  }
};

window.UserCourses = UserCourses;
