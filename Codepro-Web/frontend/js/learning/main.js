/**
 * CodeProOJ - Learning Track & Wiki Engine
 */
const LearningEngine = {
  tracks: [
    { id: 'cpp-basic', name: 'Nhập Môn Lập Trình C++ & STL', lessons: 12, completed: 8 },
    { id: 'math-algo', name: 'Toán Rời Rạc & Lý Thuyết Số', lessons: 15, completed: 5 },
    { id: 'data-structures', name: 'Cấu Trúc Dữ Liệu Nâng Cao (IT, BIT, DSU)', lessons: 18, completed: 2 },
    { id: 'dp-mastery', name: 'Quy Hoạch Động Chuyên Sâu (DP)', lessons: 24, completed: 0 },
    { id: 'graph-theory', name: 'Lý Thuyết Đồ Thị & Luồng Cực Đại', lessons: 20, completed: 0 }
  ],

  getTracks() {
    return this.tracks;
  },

  markLessonDone(lessonId) {
    const key = `lesson_done_${lessonId}`;
    localStorage.setItem(key, '1');
    if (window.Toast) Toast.success('Đã hoàn thành bài học!');
  }
};

window.LearningEngine = LearningEngine;
