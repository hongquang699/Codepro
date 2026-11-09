/**
 * CodeProOJ - Organization Service
 */
const OrganizationService = {
  async getAll() {
    try {
      const res = await fetch('/api/v2/organizations');
      const json = await res.json();
      return json.data?.items || json.data?.results || [];
    } catch (e) {
      console.error(e);
      return [];
    }
  },

  async getDetail(slug) {
    try {
      const res = await fetch(`/api/v2/organization/${slug}`);
      const json = await res.json();
      return json.data || null;
    } catch (e) {
      console.error(e);
      return null;
    }
  }
};

window.OrganizationService = OrganizationService;
