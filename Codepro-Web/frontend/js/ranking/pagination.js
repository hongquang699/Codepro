function renderPagination(total, page, pageSize, onPageChange, containerId = 'rankingPagination') {
  const container = document.getElementById(containerId);
  if (!container) return;

  const totalPages = Math.ceil(Number(total) / Number(pageSize));
  if (totalPages <= 1) {
    container.replaceChildren();
    return;
  }
  if (!Number.isSafeInteger(totalPages) || totalPages < 1) {
    container.replaceChildren();
    return;
  }
  const current = Math.min(totalPages, Math.max(1, Number(page) || 1));
  const changePage = window[onPageChange];
  if (typeof changePage !== 'function') return;
  const wrapper = document.createElement('div');
  wrapper.className = 'pagination-wrapper';
  const button = (label, target, disabled = false) => {
    const element = document.createElement('button');
    element.type = 'button';
    element.className = `page-btn${target === current ? ' active' : ''}`;
    element.textContent = label;
    element.disabled = disabled;
    element.addEventListener('click', () => changePage(target));
    wrapper.appendChild(element);
  };
  button('← Trang trước', current - 1, current <= 1);
  const pages = [...new Set([1, totalPages, current - 2, current - 1, current, current + 1, current + 2])]
    .filter(number => number >= 1 && number <= totalPages).sort((a, b) => a - b);
  let previous = 0;
  for (const number of pages) {
    if (number > previous + 1) {
      const dots = document.createElement('span');
      dots.className = 'page-dots';
      dots.textContent = '...';
      wrapper.appendChild(dots);
    }
    button(String(number), number);
    previous = number;
  }
  button('Trang sau →', current + 1, current >= totalPages);
  container.replaceChildren(wrapper);
}
window.renderPagination = renderPagination;
