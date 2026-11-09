/**
 * SubmissionStatus Component
 * Generates semantic status badges with Flaticon icons for all verdicts.
 */
const SubmissionStatus = {
  getBadge(verdict, isGrading = false) {
    const v = (verdict || 'QUEUED').toUpperCase();

    if (isGrading || ['QUEUED', 'JUDGING', 'COMPILING', 'RUNNING', 'CHECKING'].includes(v)) {
      let icon = 'fi fi-rr-spinner spin-icon';
      let text = v === 'QUEUED' ? 'Đang chờ' : (v === 'COMPILING' ? 'Đang biên dịch' : 'Đang chấm...');
      let cssClass = 'verdict-judging';
      if (v === 'QUEUED') cssClass = 'verdict-queued';

      return `<span class="status-badge ${cssClass}"><i class="${icon}"></i> ${text}</span>`;
    }

    let icon = 'fi fi-rr-cross-circle';
    let text = v;
    let cssClass = 'verdict-wa';

    switch (v) {
      case 'AC':
      case 'ACCEPTED':
        icon = 'fi fi-rr-check-circle';
        text = 'Chấp nhận (AC)';
        cssClass = 'verdict-ac';
        break;
      case 'WA':
      case 'WRONG ANSWER':
        icon = 'fi fi-rr-cross-circle';
        text = 'Kết quả sai (WA)';
        cssClass = 'verdict-wa';
        break;
      case 'TLE':
      case 'TIME LIMIT EXCEEDED':
        icon = 'fi fi-rr-clock';
        text = 'Quá thời gian (TLE)';
        cssClass = 'verdict-tle';
        break;
      case 'MLE':
      case 'MEMORY LIMIT EXCEEDED':
        icon = 'fi fi-rr-disk';
        text = 'Quá bộ nhớ (MLE)';
        cssClass = 'verdict-mle';
        break;
      case 'RTE':
      case 'RUNTIME ERROR':
        icon = 'fi fi-rr-exclamation';
        text = 'Lỗi thực thi (RTE)';
        cssClass = 'verdict-rte';
        break;
      case 'CE':
      case 'COMPILATION ERROR':
        icon = 'fi fi-rr-file-code';
        text = 'Lỗi biên dịch (CE)';
        cssClass = 'verdict-ce';
        break;
      default:
        icon = 'fi fi-rr-info';
        text = v;
        cssClass = 'verdict-queued';
    }

    return `<span class="status-badge ${cssClass}"><i class="${icon}"></i> ${text}</span>`;
  }
};

if (typeof window !== 'undefined') {
  window.SubmissionStatus = SubmissionStatus;
}
