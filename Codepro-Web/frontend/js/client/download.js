(async () => {
  const labels = {
    windows: 'Tải cho Windows (.exe)',
    'mac-arm64': 'Tải cho Apple Silicon (.dmg)',
    'mac-x64': 'Tải cho Intel (.dmg)',
    'linux-x64': 'Tải cho Linux x64 (.deb)'
  };
  const status = document.getElementById('release-status');
  let downloads = {};
  try {
    const response = await fetch('/client/releases', { cache: 'no-store' });
    if (!response.ok) throw new Error('release list unavailable');
    const data = await response.json();
    downloads = data.downloads || {};
  } catch {
    status.textContent = 'Không thể kiểm tra bản phát hành. Hãy tải lại trang sau.';
  }
  let available = 0;
  for (const [platform, label] of Object.entries(labels)) {
    const link = document.querySelector(`[data-download="${platform}"]`);
    const detail = document.querySelector(`[data-detail="${platform}"]`);
    const entry = downloads[platform];
    if (!entry) {
      link.textContent = `${label.split(' (')[0]} · Chưa phát hành`;
      detail.textContent = 'Bản cài đang được chuẩn bị.';
      continue;
    }
    available++;
    link.href = `/client/download/${platform}`;
    link.classList.remove('is-unavailable');
    link.removeAttribute('aria-disabled');
    link.textContent = label;
    detail.textContent = `v${entry.version} · ${(entry.bytes / 1024 / 1024).toFixed(1)} MB · SHA-256: ${entry.sha256}`;
  }
  if (available) status.textContent = `Đã có ${available} bản cài để tải. Chọn đúng hệ điều hành và loại chip của máy bạn.`;
  else if (!status.textContent.startsWith('Không thể')) status.textContent = 'Chưa có bản cài nào trên máy chủ. Vui lòng quay lại sau.';
})();
