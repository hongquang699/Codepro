/**
 * CodeProOJ - Contest Workspace Helpers
 */
const ContestHelper = {
  getContestKeyFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('contest') || params.get('key') || '';
  }
};

window.ContestHelper = ContestHelper;
