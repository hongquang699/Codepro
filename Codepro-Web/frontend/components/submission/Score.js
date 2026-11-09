/**
 * Score Component
 * Displays score with contextual color gradient depending on performance.
 */
const Score = {
  render(score, maxScore = 100) {
    if (score === undefined || score === null) return `<span class="score-pill">0</span>`;
    const num = parseFloat(score) || 0;
    const ratio = maxScore > 0 ? num / maxScore : 0;
    
    let color = '#ef4444'; // Red
    if (ratio >= 1.0) {
      color = '#22c55e'; // Green
    } else if (ratio >= 0.7) {
      color = '#38bdf8'; // Blue
    } else if (ratio >= 0.4) {
      color = '#eab308'; // Yellow
    }

    return `<span style="font-weight: 700; color: ${color};">${num.toFixed(1)}</span>`;
  }
};

if (typeof window !== 'undefined') {
  window.Score = Score;
}
