/**
 * SubmissionResult Component
 * Renders the top summary card of a submission.
 */
const SubmissionResult = {
  renderSummary(sub) {
    const isJudging = ['QUEUED', 'JUDGING', 'COMPILING', 'RUNNING', 'CHECKING'].includes((sub.verdict || sub.status || '').toUpperCase());
    const badge = window.SubmissionStatus ? window.SubmissionStatus.getBadge(sub.verdict || sub.status, isJudging) : (sub.verdict || sub.status);
    
    // Time & Memory normalization
    const timeMs = sub.time_ms !== undefined ? sub.time_ms : (sub.execution_time !== undefined ? sub.execution_time : 0);
    const memKb = sub.memory_kb !== undefined ? sub.memory_kb : (sub.memory_used !== undefined ? sub.memory_used * 1024 : 0);
    const timeFormatted = window.TimeMemory ? window.TimeMemory.formatTime(timeMs) : `${timeMs} ms`;
    const memFormatted = window.TimeMemory ? window.TimeMemory.formatMemory(memKb) : `${memKb} KB`;
    
    const scoreFormatted = window.Score ? window.Score.render(sub.score) : sub.score;

    // Problem code & User name normalization
    const problemCode = (typeof sub.problem === 'object' && sub.problem !== null) ? sub.problem.code : (sub.problem || 'SUMA');
    const problemName = (typeof sub.problem === 'object' && sub.problem !== null) ? (sub.problem.name || '') : '';
    const username = (typeof sub.user === 'object' && sub.user !== null) ? sub.user.username : (sub.user || 'Ẩn danh');
    const langName = (typeof sub.language === 'object' && sub.language !== null) ? sub.language.name : (sub.language || 'C++17');

    return `
      <div class="submission-summary-header">
        <div class="sub-meta-left">
          <span class="sub-id-badge"><i class="fi fi-rr-file-code"></i> Submission #${sub.id}</span>
          ${badge}
        </div>
        <div>
          <button id="btnRejudge" class="tool-btn" style="padding: 6px 14px; font-size: 0.85rem;">
            <i class="fi fi-rr-refresh"></i> Chấm lại
          </button>
        </div>
      </div>
      <div class="sub-metrics-grid">
        <div class="metric-item">
          <span class="metric-label"><i class="fi fi-rr-document"></i> Bài tập</span>
          <span class="metric-value"><a href="/problems/${problemCode}" class="sub-link" title="${problemName}">${problemCode}</a></span>
        </div>
        <div class="metric-item">
          <span class="metric-label"><i class="fi fi-rr-user"></i> Người nộp</span>
          <span class="metric-value"><a href="/users/${username}" class="sub-link">${username}</a></span>
        </div>
        <div class="metric-item">
          <span class="metric-label"><i class="fi fi-rr-terminal"></i> Ngôn ngữ</span>
          <span class="metric-value">${langName}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label"><i class="fi fi-rr-trophy"></i> Điểm</span>
          <span class="metric-value score">${scoreFormatted}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label"><i class="fi fi-rr-clock"></i> Thời gian</span>
          <span class="metric-value">${timeFormatted}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label"><i class="fi fi-rr-disk"></i> Bộ nhớ</span>
          <span class="metric-value">${memFormatted}</span>
        </div>
      </div>
    `;
  }
};

if (typeof window !== 'undefined') {
  window.SubmissionResult = SubmissionResult;
}
