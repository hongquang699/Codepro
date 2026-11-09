import glob
import os

files = glob.glob('frontend/html/admin/**/*.html', recursive=True) + glob.glob('frontend/html/admin/*.html')
count = 0
guard_tag = '  <script src="/frontend/js/core/admin-guard.js"></script>\n</head>'

for f in sorted(set(files)):
    if 'login.html' in f:
        continue
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        content = fp.read()
    if 'admin-guard.js' not in content and '</head>' in content:
        content = content.replace('</head>', guard_tag)
        with open(f, 'w', encoding='utf-8') as fp:
            fp.write(content)
        count += 1

print(f"Successfully injected admin-guard.js into {count} admin files.")
