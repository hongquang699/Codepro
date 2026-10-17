(async () => {
  const link = document.getElementById('download-link');
  const detail = document.getElementById('download-detail');
  try {
    const response = await fetch('/frontend/downloads/client-manifest.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('missing manifest');
    const manifest = await response.json();
    if (!/^\d+\.\d+\.\d+$/.test(manifest.version) ||
        manifest.file !== `CodeProOJ-Client-${manifest.version}.exe` ||
        !Number.isSafeInteger(manifest.bytes) || manifest.bytes <= 0 ||
        !/^[a-f0-9]{64}$/.test(manifest.sha256)) throw new Error('invalid manifest');
    link.classList.remove('disabled');
    link.removeAttribute('aria-disabled');
    link.textContent = `Tải cho Windows · v${manifest.version}`;
    detail.textContent = `Windows 10/11 · 64-bit · Portable · ${(manifest.bytes / 1024 / 1024).toFixed(1)} MB · SHA-256: ${manifest.sha256}`;
  } catch {
    link.textContent = 'Bản portable đang được chuẩn bị';
    detail.textContent = 'Vui lòng quay lại sau khi bản Windows được phát hành.';
  }
})();
