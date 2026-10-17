/* Public invalidation stream. Data is always fetched again through the normal API. */
(() => {
  if (typeof WebSocket === 'undefined' || !/^https?:$/.test(location.protocol)) return;
  let socket = null;
  let retry = null;
  let delay = 1000;
  let stopped = false;
  const url = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws/live`;

  function connect() {
    if (stopped) return;
    socket = new WebSocket(url);
    socket.onopen = () => { delay = 1000; window.dispatchEvent(new CustomEvent('codeprooj:live-status', { detail: { connected: true } })); };
    socket.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'invalidate' && Array.isArray(data.topics)) {
          const topics = data.topics.filter(topic => ['contests', 'problems', 'submissions', 'account'].includes(topic));
          if (topics.length) window.dispatchEvent(new CustomEvent('codeprooj:invalidate', { detail: { topics } }));
        }
      } catch { /* Ignore malformed events. */ }
    };
    socket.onerror = () => socket.close();
    socket.onclose = () => {
      window.dispatchEvent(new CustomEvent('codeprooj:live-status', { detail: { connected: false } }));
      if (!stopped) {
        retry = setTimeout(connect, delay);
        delay = Math.min(delay * 2, 30000);
      }
    };
  }

  window.addEventListener('pagehide', () => {
    stopped = true;
    clearTimeout(retry);
    if (socket) socket.close();
  });
  connect();
})();
