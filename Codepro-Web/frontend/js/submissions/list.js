/**
 * Submissions List & History Page Controller
 */
document.addEventListener('DOMContentLoaded', () => {
  const submissionsTableBody = document.getElementById('submissionsTableBody');
  const paginationControls = document.getElementById('paginationControls');
  const totalCountEl = document.getElementById('totalCount');
  
  // Filters
  const filterProblem = document.getElementById('filterProblem');
  const filterUser = document.getElementById('filterUser');
  const filterLanguage = document.getElementById('filterLanguage');
  const filterVerdict = document.getElementById('filterVerdict');
  const btnApplyFilter = document.getElementById('btnApplyFilter');
  const btnResetFilter = document.getElementById('btnResetFilter');

  let currentPage = 1;
  const pageSize = 20;

  // Initialize Language filter dropdown
  if (filterLanguage && window.LanguageSelector) {
    let opts = '<option value="">Tất cả ngôn ngữ</option>';
    window.LanguageSelector.LANGUAGES.forEach(l => {
      opts += `<option value="${l.key}">${l.label}</option>`;
    });
    filterLanguage.innerHTML = opts;
  }

  // Pre-fill filters from URL
  const params = new URLSearchParams(window.location.search);
  if (params.get('problem') && filterProblem) filterProblem.value = params.get('problem');
  if (params.get('user') && filterUser) filterUser.value = params.get('user');
  if (params.get('language') && filterLanguage) filterLanguage.value = params.get('language');
  if (params.get('verdict') && filterVerdict) filterVerdict.value = params.get('verdict');
  if (params.get('page')) currentPage = parseInt(params.get('page'), 10) || 1;

  loadSubmissions();
  window.addEventListener('codeprooj:invalidate', event => {
    if (event.detail?.topics?.includes('submissions')) loadSubmissions();
  });

  if (btnApplyFilter) {
    btnApplyFilter.addEventListener('click', () => {
      currentPage = 1;
      loadSubmissions();
    });
  }

  if (btnResetFilter) {
    btnResetFilter.addEventListener('click', () => {
      if (filterProblem) filterProblem.value = '';
      if (filterUser) filterUser.value = '';
      if (filterLanguage) filterLanguage.value = '';
      if (filterVerdict) filterVerdict.value = '';
      currentPage = 1;
      loadSubmissions();
    });
  }

  async function loadSubmissions() {
    const query = new URLSearchParams({
      page: currentPage,
      page_size: pageSize
    });

    if (filterProblem && filterProblem.value.trim()) query.append('problem', filterProblem.value.trim().toUpperCase());
    if (filterUser && filterUser.value.trim()) query.append('user', filterUser.value.trim());
    if (filterLanguage && filterLanguage.value) query.append('language', filterLanguage.value);
    if (filterVerdict && filterVerdict.value) query.append('verdict', filterVerdict.value);

    // Contextual URL support (e.g. contest)
    const contestParam = params.get('contest');
    if (contestParam) query.append('contest', contestParam);

    try {
      if (submissionsTableBody) {
        submissionsTableBody.innerHTML = `
          <tr>
            <td colspan="9" style="text-align: center; padding: 40px; color: var(--color-text-muted);">
              <i class="fi fi-rr-spinner spin-icon" style="font-size: 1.5rem; display: block; margin-bottom: 8px;"></i>
              Đang tải danh sách bài nộp...
            </td>
          </tr>
        `;
      }

      const res = await fetch(`/api/v1/submissions/?${query.toString()}`);
      if (!res.ok) throw new Error("Fetch failed");

      const data = await res.json();
      renderTable(data);
    } catch (err) {
      if (submissionsTableBody) {
        submissionsTableBody.innerHTML = `
          <tr>
            <td colspan="9" style="text-align: center; padding: 30px; color: #f87171;">
              Không thể tải dữ liệu bài nộp. Vui lòng thử lại sau.
            </td>
          </tr>
        `;
      }
    }
  }

  function renderTable(data) {
    const items = data.items || [];
    if (submissionsTableBody && window.SubmissionTable) {
      submissionsTableBody.innerHTML = window.SubmissionTable.renderTable(items);
    }

    if (totalCountEl) {
      totalCountEl.textContent = `${data.total || 0} bài nộp`;
    }

    renderPagination(data.page || 1, data.total_pages || 1);
  }

  function renderPagination(page, totalPages) {
    if (!paginationControls) return;
    if (totalPages <= 1) {
      paginationControls.innerHTML = '';
      return;
    }

    let html = `
      <button class="page-btn" ${page <= 1 ? 'disabled' : ''} data-page="${page - 1}">
        <i class="fi fi-rr-angle-left"></i> Trước
      </button>
      <div class="pagination-pages">
    `;

    for (let p = Math.max(1, page - 2); p <= Math.min(totalPages, page + 2); p++) {
      html += `
        <button class="page-btn ${p === page ? 'active' : ''}" data-page="${p}">${p}</button>
      `;
    }

    html += `
      </div>
      <button class="page-btn" ${page >= totalPages ? 'disabled' : ''} data-page="${page + 1}">
        Sau <i class="fi fi-rr-angle-right"></i>
      </button>
    `;

    paginationControls.innerHTML = html;

    paginationControls.querySelectorAll('.page-btn:not(:disabled)').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetPage = parseInt(btn.dataset.page, 10);
        if (targetPage && targetPage !== currentPage) {
          currentPage = targetPage;
          loadSubmissions();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    });
  }
});
