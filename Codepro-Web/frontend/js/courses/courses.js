/**
 * CodeProOJ - Courses Engine
 */
const CoursesEngine = {
  async getCourses() {
    return [
      { id: 'cpp', title: 'Lập trình C++ Cơ bản đến Nâng cao', level: 'Nhập môn', lessons_count: 24, instructor: 'CodeProOJ Coach' },
      { id: 'dsa', title: 'Cấu trúc dữ liệu & Giải thuật cho HSG', level: 'Trung cấp', lessons_count: 36, instructor: 'Master Red' },
      { id: 'icpc', title: 'Luyện thi ICPC & Olympic Tin học', level: 'Chuyên sâu', lessons_count: 40, instructor: 'ICPC World Finalist' }
    ];
  }
};

window.CoursesEngine = CoursesEngine;
