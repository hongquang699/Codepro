/**
 * CodeProOJ - Organizations Directory Main Script
 */
document.addEventListener('DOMContentLoaded', () => {
  if (typeof OrganizationService !== 'undefined' && typeof renderOrgs === 'function') {
    OrganizationService.getAll().then(renderOrgs);
  }
});
