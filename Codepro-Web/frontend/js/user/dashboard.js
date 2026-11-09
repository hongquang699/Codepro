/**
 * CodeProOJ - User Personal Dashboard Controller
 */
const UserDashboard = {
  async init() {
    const user = Auth ? Auth.getUser() : null;
    if (!user) {
      window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
      return;
    }
  }
};

window.UserDashboard = UserDashboard;
