/**
 * CodeProOJ Home Dashboard Integration
 * Loads live platform metrics, featured contest, problems, top coders, recent submissions, and news
 */

function getRankColor(rating) {
  if (typeof CPRating !== 'undefined') return CPRating.getColor(rating);
  const r = parseInt(rating, 10);
  if (isNaN(r) || r <= 0) return '#94a3b8'; // Unrated / 0 rating -> Gray
  if (r >= 2400) return '#ef4444'; // Grandmaster
  if (r >= 2100) return '#f97316'; // Master
  if (r >= 1900) return '#a855f7'; // Candidate Master
  if (r >= 1600) return '#3b82f6'; // Expert
  if (r >= 1400) return '#10b981'; // Specialist
  if (r >= 1200) return '#06b6d4'; // Pupil
  return '#94a3b8'; // Newbie
}
async function initHomePage() {
  const API_BASE = (typeof window.API_BASE === 'string')
    ? window.API_BASE
    : (window.location.origin && window.location.origin.startsWith('http') ? '' : 'http://localhost:8000');

  try {
    const res = await fetch(`${API_BASE}/api/v1/home/summary`);
    const data = await res.json();
    if (data.status !== 'success') return;

    // 1. Platform Statistics
    const st = data.stats || {};
    if (document.getElementById('statUsers')) document.getElementById('statUsers').textContent = st.users || 12;
    if (document.getElementById('statProblems')) document.getElementById('statProblems').textContent = st.problems || 9;
    if (document.getElementById('statSubmissions')) document.getElementById('statSubmissions').textContent = st.submissions || 53;
    if (document.getElementById('statContests')) document.getElementById('statContests').textContent = st.contests || 2;

    // 2. Featured Problems
    const probTbody = document.getElementById('homeProblemsBody');
    if (probTbody) {
      const probs = data.featured_problems || [];
      if (probs.length === 0) {
        probTbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #94a3b8; padding: 2rem;">Chưa có bài tập.</td></tr>';
      } else {
        probTbody.innerHTML = probs.map(p => `
          <tr>
            <td>
              <a href="/problems/${p.code}" style="font-family: monospace; font-weight: 700; color: #38bdf8; text-decoration: none;">
                ${p.code}
              </a>
            </td>
            <td>
              <a href="/problems/${p.code}" style="color: #f8fafc; font-weight: 600; text-decoration: none;">
                ${p.name}
              </a>
            </td>
            <td style="text-align: center;">
              <span class="badge" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; font-weight: 700;">
                ★ ${p.difficulty}
              </span>
            </td>
            <td style="text-align: center; font-weight: 700; color: #10b981;">
              ${p.points}
            </td>
            <td style="text-align: center; font-weight: 600; color: #cbd5e1;">
              ${p.ac_rate}% <span style="font-size: 0.75rem; color: #94a3b8;">(${p.ac_count})</span>
            </td>
          </tr>
        `).join('');
      }
    }

    // 3. Featured Contest
    const contestBox = document.getElementById('homeContestCard');
    const fc = data.featured_contest;
    if (contestBox) {
      if (fc) {
        const badge = document.getElementById('contestStatusBadge');
        if (badge) {
          badge.textContent = fc.status_display || fc.status;
          if (fc.status === 'RUNNING') {
            badge.className = 'badge badge-ac';
          } else if (fc.status === 'UPCOMING') {
            badge.className = 'badge badge-pending';
          } else {
            badge.className = 'badge';
            badge.style.background = '#334155';
            badge.style.color = '#cbd5e1';
          }
        }

        contestBox.innerHTML = `
          <h3 style="margin: 0 0 0.5rem 0; font-size: 1.15rem;">
            <a href="/contests/${fc.key}" style="color: #fff; text-decoration: none; font-weight: 800;">
              ${fc.name}
            </a>
          </h3>
          <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.75rem;">
            Thể thức: <strong>${fc.format}</strong> • Số bài: <strong>${fc.problem_count}</strong> bài
          </div>
          <a href="/contests/${fc.key}" class="btn btn-primary" style="width: 100%; text-align: center; display: block; padding: 0.6rem 1rem; font-weight: 700; text-decoration: none; border-radius: 8px;">
            Tham gia cuộc thi &rarr;
          </a>
        `;
      } else {
        const badge = document.getElementById('contestStatusBadge');
        if (badge) badge.style.display = 'none';
        contestBox.innerHTML = `
          <div style="text-align: center; color: #94a3b8; padding: 1.5rem 0;">
            <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">🏆</div>
            <div style="font-weight: 600; color: #cbd5e1; margin-bottom: 0.25rem;">Chưa có kỳ thi nào diễn ra</div>
            <div style="font-size: 0.82rem; color: #64748b;">Các kỳ thi thuật toán sắp tới sẽ được cập nhật tại đây.</div>
          </div>
        `;
      }
    }

    // 4. Top Coders Leaderboard
    const topTbody = document.getElementById('homeTopUsersBody');
    if (topTbody) {
      const users = data.top_users || [];
      if (users.length === 0) {
        topTbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #94a3b8;">Chưa có dữ liệu.</td></tr>';
      } else {
        topTbody.innerHTML = users.map((u, i) => {
          const color = getRankColor(u.rating);
          return `
            <tr>
              <td style="font-weight: 800; color: #94a3b8;">#${i + 1}</td>
              <td>
                <a href="/profile/${encodeURIComponent(u.username)}" style="color: ${color}; font-weight: 700; text-decoration: none;">
                  ${u.username}
                </a>
                <div style="font-size: 0.75rem; color: #64748b;">${u.rank}</div>
              </td>
              <td style="text-align: right; font-weight: 800; color: ${color}; font-family: monospace;">
                ${u.rating}
              </td>
            </tr>
          `;
        }).join('');
      }
    }

    // 5. Recent Submissions Widget
    const recentSubsBox = document.getElementById('homeRecentSubs');
    if (recentSubsBox) {
      const subs = data.recent_submissions || [];
      if (subs.length === 0) {
        recentSubsBox.innerHTML = '<div style="color: #94a3b8; padding: 0.5rem 0;">Chưa có bài nộp nào.</div>';
      } else {
        recentSubsBox.innerHTML = subs.map(s => {
          const isAC = (s.result === 'AC');
          const pillColor = isAC ? '#10b981' : '#ef4444';
          const pillBg = isAC ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';

          return `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
              <div>
                <a href="/problems/${s.problem_code}" style="color: #38bdf8; font-weight: 700; text-decoration: none; font-family: monospace;">
                  ${s.problem_code}
                </a>
                <span style="color: #94a3b8; font-size: 0.78rem; margin-left: 0.25rem;">bởi</span>
                <a href="/profile/${encodeURIComponent(s.user)}" style="color: #cbd5e1; font-weight: 600; text-decoration: none; font-size: 0.82rem;">
                  ${s.user}
                </a>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="background: ${pillBg}; color: ${pillColor}; font-weight: 800; font-size: 0.75rem; padding: 0.15rem 0.45rem; border-radius: 4px; font-family: monospace;">
                  ${s.result}
                </span>
                <span style="color: #64748b; font-size: 0.75rem;">${s.time_ms != null ? s.time_ms + 'ms' : ''}</span>
              </div>
            </div>
          `;
        }).join('');
      }
    }

    // 6. News & Announcements
    const newsBox = document.getElementById('homeAnnouncements');
    if (newsBox) {
      const news = data.announcements || [];
      newsBox.innerHTML = news.map(item => `
        <article style="background: #0f172a; border: 1px solid var(--home-border); border-radius: 10px; padding: 1.1rem 1.25rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
            <span style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; font-weight: 700; font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 4px;">
              ${item.tag}
            </span>
            <span style="font-size: 0.78rem; color: #64748b;">${item.date}</span>
          </div>
          <h3 style="margin: 0 0 0.35rem 0; font-size: 1.05rem;">
            <a href="${item.link}" style="color: #f8fafc; text-decoration: none; font-weight: 700;">
              ${item.title}
            </a>
          </h3>
          <p style="color: #94a3b8; font-size: 0.88rem; line-height: 1.5; margin: 0;">
            ${item.summary}
          </p>
        </article>
      `).join('');
    }
  } catch (err) {
    console.error('Error fetching home summary:', err);
  }
}

document.addEventListener('DOMContentLoaded', initHomePage);
