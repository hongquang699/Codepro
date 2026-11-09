/**
 * CodeProOJ - Global Ranking Helpers
 */
const RankingHelper = {
  getRankBadge(rating) {
    if (typeof CPRating !== 'undefined') {
      const t = CPRating.getTier(rating);
      return { name: t.name, color: t.color, class: t.class };
    }
    const r = parseInt(rating, 10) || 0;
    if (r >= 2400) return { name: 'Grandmaster', color: '#ef4444', class: 'rank-gm' };
    if (r >= 2100) return { name: 'Master', color: '#f97316', class: 'rank-master' };
    if (r >= 1900) return { name: 'Candidate Master', color: '#a855f7', class: 'rank-cm' };
    if (r >= 1600) return { name: 'Expert', color: '#3b82f6', class: 'rank-expert' };
    if (r >= 1400) return { name: 'Specialist', color: '#10b981', class: 'rank-specialist' };
    if (r >= 1200) return { name: 'Pupil', color: '#06b6d4', class: 'rank-pupil' };
    return { name: 'Newbie', color: '#94a3b8', class: 'rank-newbie' };
  }
};

window.RankingHelper = RankingHelper;
