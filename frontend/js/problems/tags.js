/**
 * CodeProOJ - Algorithm Tags Logic
 * Loads problem categories, counts problem frequency,
 * and renders category cards with direct filter links.
 */

(() => {
  const API = (typeof window.API_BASE === 'string')
    ? window.API_BASE
    : (window.location.origin && window.location.origin.startsWith('http') ? '' : 'http://localhost:8000');

  const defaultTags = [
    { name: 'Cơ bản', desc: 'Nhập môn lập trình, rẽ nhánh, vòng lặp, mảng 1 chiều', count: 3 },
    { name: 'Toán học', desc: 'Số học, ước chung lớn nhất, số nguyên tố, đồng dư, tổ hợp', count: 2 },
    { name: 'Quy hoạch động', desc: 'DP cơ bản, cái túi (Knapsack), dãy con tăng dài nhất', count: 1 },
    { name: 'Đồ thị', desc: 'BFS, DFS, Dijkstra, Floyd, Cây khung nhỏ nhất', count: 1 },
    { name: 'Cấu trúc dữ liệu', desc: 'Stack, Queue, Segment Tree, Fenwick Tree, Disjoint Set', count: 1 },
    { name: 'Tham lam', desc: 'Greedy algorithms, sắp xếp thời gian, tối ưu hóa cục bộ', count: 1 },
    { name: 'Chuỗi (String)', desc: 'Xử lý xâu, KMP, Hashing, Trie', count: 1 },
    { name: 'Hình học tính toán', desc: 'Giao điểm, bao lồi, diện tích đa giác', count: 1 }
  ];

  async function loadTags() {
    const grid = document.getElementById('tagGrid');
    if (!grid) return;

    try {
      const resp = await fetch(`${API}/api/v2/problems`);
      const json = await resp.json();
      const probs = json?.data?.objects || [];

      const tagCountMap = {};
      probs.forEach(p => {
        (p.types || []).forEach(t => {
          const name = typeof t === 'string' ? t : t.name;
          tagCountMap[name] = (tagCountMap[name] || 0) + 1;
        });
      });

      grid.innerHTML = defaultTags.map(t => {
        const cnt = tagCountMap[t.name] || t.count;
        return `
          <a href="/frontend/html/problem/index.html?tag=${encodeURIComponent(t.name)}" class="tag-card">
            <div class="tag-info">
              <h3>🏷 ${t.name}</h3>
              <p>${t.desc}</p>
            </div>
            <div class="tag-count">${cnt}</div>
          </a>
        `;
      }).join('');
    } catch (err) {
      console.warn('Error loading tags:', err);
    }
  }

  document.addEventListener('DOMContentLoaded', loadTags);
})();
