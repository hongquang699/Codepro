"""Vendor the two commonly used font weights for fast, reliable page loads."""

import re
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / 'frontend' / 'assets' / 'fonts'
CSS_PATH = ROOT / 'frontend' / 'css' / 'global' / 'fonts.css'
FONT_CSS_URL = (
    'https://fonts.googleapis.com/css2?'
    'family=Be+Vietnam+Pro:wght@400;700&'
    'family=Inter:wght@400;700&'
    'family=JetBrains+Mono:wght@400;700&display=swap'
)
LICENSES = {
    'Be-Vietnam-Pro': 'bevietnampro',
    'Inter': 'inter',
    'JetBrains-Mono': 'jetbrainsmono',
}


def download(url):
    request = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    })
    with urlopen(request, timeout=20) as response:
        return response.read()


def main():
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    css = download(FONT_CSS_URL).decode('utf-8')
    output = ['/* Self-hosted Google Fonts; licenses are in /frontend/assets/fonts/. */']
    count = 0
    for subset, body in re.findall(r'/\*\s*([^*]+?)\s*\*/\s*@font-face\s*\{([^}]+)\}', css):
        subset = subset.strip()
        if subset not in ('vietnamese', 'latin-ext', 'latin'):
            continue
        family = re.search(r"font-family:\s*'([^']+)'", body).group(1)
        weight = re.search(r'font-weight:\s*(\d+)', body).group(1)
        source = re.search(r'url\((https://[^)]+\.woff2)\)', body).group(1)
        unicode_range = re.search(r'unicode-range:\s*([^;]+);', body).group(1)
        name = f'{family.lower().replace(" ", "-")}-{weight}-{subset}.woff2'
        data = download(source)
        if not data.startswith(b'wOF2'):
            raise RuntimeError(f'Unexpected font format: {source}')
        (FONT_DIR / name).write_bytes(data)
        output.extend([
            f'/* {subset} */',
            '@font-face {',
            f"  font-family: '{family}';",
            '  font-style: normal;',
            f'  font-weight: {weight};',
            '  font-display: swap;',
            f"  src: url('/frontend/assets/fonts/{name}') format('woff2');",
            f'  unicode-range: {unicode_range};',
            '}',
        ])
        count += 1
    if count < 12:
        raise RuntimeError(f'Expected at least 12 font subsets, got {count}')
    CSS_PATH.write_text('\n'.join(output) + '\n', encoding='utf-8')
    for label, directory in LICENSES.items():
        license_url = f'https://raw.githubusercontent.com/google/fonts/main/ofl/{directory}/OFL.txt'
        (FONT_DIR / f'OFL-{label}.txt').write_bytes(download(license_url))
    print(f'Vendored {count} WOFF2 subsets and {len(LICENSES)} licenses')


if __name__ == '__main__':
    main()
