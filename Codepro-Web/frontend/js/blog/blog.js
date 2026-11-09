/**
 * CodeProOJ - Blog API & Service
 */
const BlogService = {
  async getPosts(tag = '') {
    try {
      const url = tag ? `/api/v2/blogs?tag=${encodeURIComponent(tag)}` : '/api/v2/blogs';
      const res = await fetch(url);
      const json = await res.json();
      return json.data?.items || json.data?.results || [];
    } catch (e) {
      console.error(e);
      return [];
    }
  },

  async getDetail(slug) {
    try {
      const res = await fetch(`/api/v2/blog/${slug}`);
      const json = await res.json();
      return json.data || null;
    } catch (e) {
      console.error(e);
      return null;
    }
  }
};

window.BlogService = BlogService;
