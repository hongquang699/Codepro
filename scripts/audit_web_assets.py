"""Check local resources referenced by every frontend HTML page through the gateway."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
import re
from statistics import median
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8888'


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'img', 'source'):
            value = attrs.get('src')
        elif tag == 'link' and attrs.get('rel') in ('stylesheet', 'icon', 'preload'):
            value = attrs.get('href')
        else:
            return
        if value and value.startswith('/') and not value.startswith('//'):
            path = urlsplit(value).path
            if '{' not in path and '}' not in path:
                self.paths.add(path)


def check(path):
    started = perf_counter()
    try:
        with urlopen(BASE + path, timeout=8) as response:
            response.read(1024)
            return path, response.status, perf_counter() - started
    except HTTPError as error:
        return path, error.code, perf_counter() - started
    except (URLError, TimeoutError) as error:
        return path, str(error), perf_counter() - started


def main():
    pages = sorted((ROOT / 'frontend' / 'html').rglob('*.html'))
    assets = set()
    for page in pages:
        parser = Resources()
        parser.feed(page.read_text(encoding='utf-8', errors='replace'))
        assets.update(parser.paths)
    for stylesheet in (ROOT / 'frontend' / 'css').rglob('*.css'):
        css = stylesheet.read_text(encoding='utf-8', errors='replace')
        for value in re.findall(r'''url\(\s*['"]?(/[^)'"\s]+)''', css):
            assets.add(urlsplit(value).path)

    paths = [f'/frontend/html/{page.relative_to(ROOT / "frontend" / "html").as_posix()}' for page in pages]
    paths.extend(sorted(assets))
    results = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for future in as_completed(pool.submit(check, path) for path in paths):
            results.append(future.result())

    failures = sorted(result for result in results if result[1] != 200)
    timings = sorted(elapsed for _, status, elapsed in results if status == 200)
    print(f'pages={len(pages)} assets={len(assets)} checked={len(results)} failures={len(failures)}')
    if timings:
        print(f'median={median(timings):.3f}s p95={timings[int(len(timings) * .95)]:.3f}s max={timings[-1]:.3f}s')
    for path, status, elapsed in failures[:100]:
        print(f'{status} {elapsed:.3f}s {path}')


if __name__ == '__main__':
    main()
