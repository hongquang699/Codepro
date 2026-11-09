/**
 * TestcaseResult Component
 * Renders individual testcase result rows in the submission detail view.
 */
const TestcaseResult = {
  renderRow(tc) {
    const verdict = (tc.verdict || 'PENDING').toUpperCase();
    const isAC = verdict === 'AC' || verdict === 'ACCEPTED';
    
    let statusBadge = `<span class="status-badge verdict-wa">${verdict}</span>`;
    if (isAC) {
      statusBadge = `<span class="status-badge verdict-ac"><i class="fi fi-rr-check"></i> AC</span>`;
    } else if (verdict === 'TLE') {
      statusBadge = `<span class="status-badge verdict-tle"><i class="fi fi-rr-clock"></i> TLE</span>`;
    } else if (verdict === 'MLE') {
      statusBadge = `<span class="status-badge verdict-mle"><i class="fi fi-rr-disk"></i> MLE</span>`;
    } else if (verdict === 'RTE') {
      statusBadge = `<span class="status-badge verdict-rte"><i class="fi fi-rr-exclamation"></i> RTE</span>`;
    }

    const timeFormatted = window.TimeMemory ? window.TimeMemory.formatTime(tc.time_ms) : `${tc.time_ms || 0} ms`;
    const memFormatted = window.TimeMemory ? window.TimeMemory.formatMemory(tc.memory_kb) : `${tc.memory_kb || 0} KB`;
    const scoreFormatted = (tc.score !== undefined && tc.score !== null) ? Number(tc.score).toFixed(1) : '0.0';

    return `
      <tr>
        <td><strong>#${tc.test_number || tc.id}</strong></td>
        <td>${statusBadge}</td>
        <td>${timeFormatted}</td>
        <td>${memFormatted}</td>
        <td><strong style="color: ${isAC ? '#22c55e' : '#94a3b8'};">${scoreFormatted}</strong></td>
        <td><span style="color: var(--color-text-muted); font-size: 0.85rem;">${tc.message || (isAC ? 'Chính xác' : 'Sai')}</span></td>
      </tr>
    `;
  }
};

if (typeof window !== 'undefined') {
  window.TestcaseResult = TestcaseResult;
}
