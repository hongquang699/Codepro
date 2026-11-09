const fs = require('fs');
const path = require('path');

function walk(dir, ext) {
  let res = [];
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    const full = path.join(dir, file);
    const stat = fs.statSync(full);
    if (stat && stat.isDirectory()) {
      res = res.concat(walk(full, ext));
    } else if (file.endsWith(ext)) {
      res.push(full);
    }
  });
  return res;
}

const htmlFiles = walk('c:/Users/admin/HQ/frontend/html', '.html');
let updatedCount = 0;

htmlFiles.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let changed = false;

  if (!content.includes('/frontend/css/global/theme.css')) {
    if (content.includes('</head>')) {
      content = content.replace('</head>', '  <link rel="stylesheet" href="/frontend/css/global/theme.css">\n</head>');
      changed = true;
    } else if (content.includes('</HEAD>')) {
      content = content.replace('</HEAD>', '  <link rel="stylesheet" href="/frontend/css/global/theme.css">\n</HEAD>');
      changed = true;
    }
  }

  if (!content.includes('/frontend/js/core/theme.js')) {
    if (content.includes('</body>')) {
      content = content.replace('</body>', '  <script src="/frontend/js/core/theme.js"></script>\n</body>');
      changed = true;
    } else if (content.includes('</BODY>')) {
      content = content.replace('</BODY>', '  <script src="/frontend/js/core/theme.js"></script>\n</BODY>');
      changed = true;
    }
  }

  if (!content.includes('/frontend/js/core/i18n.js')) {
    if (content.includes('</body>')) {
      content = content.replace('</body>', '  <script src="/frontend/js/core/i18n.js"></script>\n</body>');
      changed = true;
    } else if (content.includes('</BODY>')) {
      content = content.replace('</BODY>', '  <script src="/frontend/js/core/i18n.js"></script>\n</BODY>');
      changed = true;
    }
  }

  if (changed) {
    fs.writeFileSync(file, content, 'utf8');
    updatedCount++;
  }
});

console.log('Batch synchronized', updatedCount, 'HTML files with theme.css, theme.js, and i18n.js');
