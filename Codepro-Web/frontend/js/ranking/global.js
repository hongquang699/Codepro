let currentPage = 1;
const pageSize = 50;

async function loadGlobalRankings(page = 1) {
  currentPage = page;
  const search = document.getElementById('filterSearch') ? document.getElementById('filterSearch').value.trim() : '';
  const country = document.getElementById('filterCountry') ? document.getElementById('filterCountry').value : '';

  try {
    const data = await window.RankingApi.fetchGlobalRankings({
      page: currentPage,
      page_size: pageSize,
      search,
      country
    });

    if (window.renderRankingTable) {
      window.renderRankingTable(data.items, 'rankingTableBody');
    }

    if (window.renderPagination) {
      window.renderPagination(data.total, currentPage, pageSize, 'loadGlobalRankings', 'rankingPagination');
    }
  } catch (err) {
    const tbody = document.getElementById('rankingTableBody');
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #ef4444; padding: 30px;">Lỗi tải dữ liệu: ${window.escapeRankingHtml(err.message)}</td></tr>`;
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadGlobalRankings(1);

  const searchInput = document.getElementById('filterSearch');
  const countrySelect = document.getElementById('filterCountry');

  if (countrySelect) countrySelect.addEventListener('change', () => loadGlobalRankings(1));
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => loadGlobalRankings(1), 300);
    });
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        clearTimeout(debounceTimer);
        loadGlobalRankings(1);
      }
    });
  }
});

window.loadGlobalRankings = loadGlobalRankings;
