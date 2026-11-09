/**
 * CodeProOJ - Universal Pagination Generator
 */
const PaginationUtils = {
  render({ currentPage, totalPages, onPageChange, containerId }) {
    const container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
    if (!container || totalPages <= 1) {
      if (container) container.innerHTML = '';
      return;
    }

    let html = '<div class="pagination-bar" style="display:flex;gap:0.4rem;align-items:center;justify-content:center;margin-top:1.5rem;">';

    // Prev button
    if (currentPage > 1) {
      html += `<button class="btn-act" onclick="${onPageChange}(${currentPage - 1})">&larr; Trước</button>`;
    }

    // Page numbers
    const start = Math.max(1, currentPage - 2);
    const end = Math.min(totalPages, currentPage + 2);

    if (start > 1) {
      html += `<button class="btn-act" onclick="${onPageChange}(1)">1</button>`;
      if (start > 2) html += '<span style="color: var(--color-text-dim);padding:0 0.25rem;">...</span>';
    }

    for (let p = start; p <= end; p++) {
      const activeStyle = p === currentPage ? 'background: var(--color-primary);color: #fff;border-color: var(--color-primary);' : '';
      html += `<button class="btn-act" style="${activeStyle}" onclick="${onPageChange}(${p})">${p}</button>`;
    }

    if (end < totalPages) {
      if (end < totalPages - 1) html += '<span style="color: var(--color-text-dim);padding:0 0.25rem;">...</span>';
      html += `<button class="btn-act" onclick="${onPageChange}(${totalPages})">${totalPages}</button>`;
    }

    // Next button
    if (currentPage < totalPages) {
      html += `<button class="btn-act" onclick="${onPageChange}(${currentPage + 1})">Sau &rarr;</button>`;
    }

    html += '</div>';
    container.innerHTML = html;
  }
};

window.PaginationUtils = PaginationUtils;
