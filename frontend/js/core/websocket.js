/** Read-only subscription client for individual submission status updates. */
class SubmissionSocket {
  constructor(baseUrl = CONFIG.WS_URL) {
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
    this.sockets = new Map();
  }

  connect(submissionId, callback) {
    return this.subscribe(submissionId, callback);
  }

  subscribe(submissionId, callback) {
    const id = String(submissionId);
    if (!/^[1-9][0-9]*$/.test(id)) throw new Error('Invalid submission ID');
    this.unsubscribe(id);
    const socket = new WebSocket(`${this.baseUrl}${id}/`);
    this.sockets.set(id, socket);
    socket.onmessage = event => {
      try {
        callback(JSON.parse(event.data));
      } catch (error) {
        console.error('Submission WebSocket message error:', error);
      }
    };
    socket.onclose = () => {
      if (this.sockets.get(id) === socket) this.sockets.delete(id);
    };
    return () => this.unsubscribe(id);
  }

  unsubscribe(submissionId) {
    const id = String(submissionId);
    const socket = this.sockets.get(id);
    if (!socket) return;
    this.sockets.delete(id);
    socket.close();
  }
}

const submissionSocket = new SubmissionSocket();
