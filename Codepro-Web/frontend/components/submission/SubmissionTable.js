/**
 * SubmissionTable Component
 * Generates submission history rows and full table rendering.
 */
const SubmissionTable = {
  renderRow(sub) {
    const isJudging = ['QUEUED', 'JUDGING', 'COMPILING', 'RUNNING', 'CHECKING'].includes((sub.verdict || '').toUpperCase());
    const badge = window.SubmissionStatus ? window.SubmissionStatus.getBadge(sub.verdict, isJudging) : sub.verdict;
    const timeFormatted = window.TimeMemory ? window.TimeMemory.formatTime(sub.time_ms) : `${sub.time_ms || 0} ms`;
    const memFormatted = window.TimeMemory ? window.TimeMemory.formatMemory(sub.memory_kb) : `${sub.memory_kb || 0} KB`;
    const scoreFormatted = window.Score ? window.Score.render(sub.score) : sub.score;
    const dateFormatted = sub.created_at ? new Date(sub.created_at).toLocaleString('vi-VN') : '-';

    return `
      <tr data-sub-id="${sub.id}">
        <td><a href="/submissions/${sub.id}" class="sub-link">#${sub.id}</a></td>
        <td><a href="/profile/${encodeURIComponent(sub.user)}" class="sub-link">${sub.user}</a></td>
        <td><a href="/problems/${sub.problem}" class="sub-link" title="${sub.problem_name || ''}">${sub.problem}</a></td>
        <td>${badge}</td>
        <td>${scoreFormatted}</td>
        <td>${sub.language || 'C++17'}</td>
        <td>${timeFormatted}</td>
        <td>${memFormatted}</td>
        <td style="color: var(--color-text-muted); font-size: 0.85rem;">${dateFormatted}</td>
      </tr>
    `;
  },

  renderTable(items) {
    if (!items || items.length === 0) {
      return `
        <tr>
          <td colspan="9" style="text-align: center; padding: 40px; color: var(--color-text-muted);">
            <i class="fi fi-rr-inbox" style="font-size: 2rem; display: block; margin-bottom: 8px;"></i>
            Không tìm thấy bài nộp nào
          </td>
        </tr>
      `;
    }
    return items.map(sub => this.renderRow(sub)).join('');
  }
};

if (typeof window !== 'undefined') {
  window.SubmissionTable = SubmissionTable;
}
