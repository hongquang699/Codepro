module.exports = {
  port: process.env.PORT || 4000,
  jwtSecret: process.env.JWT_SECRET || 'dev_secret_2026',
  storageRoot: process.env.STORAGE_ROOT || './storage'
};
