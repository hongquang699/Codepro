/**
 * Submissions Status Poller & Event Tracker
 */
const SubmissionStatusTracker = {
  track(submissionId, onStatusChange) {
    const wsClient = new window.SubmissionWebSocket(submissionId, (update) => {
      if (onStatusChange) onStatusChange(update);
    });
    wsClient.connect();
    return wsClient;
  }
};

if (typeof window !== 'undefined') {
  window.SubmissionStatusTracker = SubmissionStatusTracker;
}
