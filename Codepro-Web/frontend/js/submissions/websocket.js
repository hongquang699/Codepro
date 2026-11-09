/**
 * Submissions WebSocket Client
 * Realtime subscription to submission grading events with graceful HTTP polling fallback.
 */
class SubmissionWebSocket {
  constructor(submissionId, onUpdate) {
    this.submissionId = submissionId;
    this.onUpdate = onUpdate;
    this.ws = null;
    this.pollTimer = null;
    this.isClosed = false;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/submissions/${this.submissionId}/`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (this.onUpdate) this.onUpdate(data);
          if (data.finished || data.status === 'FINISHED') {
            this.disconnect();
          }
        } catch (e) {
          console.error("WS Parse error", e);
        }
      };

      this.ws.onerror = () => {
        // Fallback to polling
        this.startPolling();
      };

      this.ws.onclose = () => {
        if (!this.isClosed) {
          this.startPolling();
        }
      };
    } catch (e) {
      this.startPolling();
    }
  }

  startPolling() {
    if (this.pollTimer || this.isClosed) return;
    this.pollTimer = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/submissions/${this.submissionId}/status/`);
        if (res.ok) {
          const data = await res.json();
          if (this.onUpdate) this.onUpdate(data);
          if (data.finished || data.status === 'FINISHED') {
            this.disconnect();
          }
        }
      } catch (err) {
        console.warn("Polling error", err);
      }
    }, 1500);
  }

  disconnect() {
    this.isClosed = true;
    if (this.ws) {
      try { this.ws.close(); } catch (e) {}
      this.ws = null;
    }
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }
}

if (typeof window !== 'undefined') {
  window.SubmissionWebSocket = SubmissionWebSocket;
}
