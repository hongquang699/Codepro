/**
 * CodeProOJ - Teacher & Classroom Manager
 */
const TeacherManager = {
  getClasses() {
    return [
      { id: '10tin', name: 'Lớp 10 Chuyên Tin', students: 28, assignments: 14 },
      { id: '11tin', name: 'Lớp 11 Chuyên Tin', students: 25, assignments: 22 },
      { id: '12tin', name: 'Đội tuyển HSG Quốc Gia', students: 8, assignments: 45 }
    ];
  }
};

window.TeacherManager = TeacherManager;
