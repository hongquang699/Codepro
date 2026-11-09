module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2022: true,
    jest: true,
  },
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'script',
  },
  overrides: [
    {
      files: ['apps/client/renderer/*-entry.js'],
      parserOptions: { sourceType: 'module' },
    },
  ],
  rules: {
    'no-unexpected-multiline': 'error',
  },
};
