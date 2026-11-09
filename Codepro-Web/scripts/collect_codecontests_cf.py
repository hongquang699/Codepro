"""Collect deterministic Codeforces tasks from the CC BY 4.0 CodeContests dataset.

This command only writes a reviewable JSONL manifest. It does not modify the OJ.
"""
import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from problem_data_path import data_root

API = 'https://datasets-server.huggingface.co/rows'
DATASET = 'deepmind/code_contests'
BATCH = 20
EXCLUDE = re.compile(
    r'interactive problem|print any|output any|any valid|any order|'
    r'if there are multiple answers|if multiple answers exist|'
    r'if there are several answers|you may output any|'
    r'you can output any|any of them|'
    r'output one of|print one of|'
    r'answer in any order|'
    r'one of the possible|'
    r'print -1 or|'
    r'output -1 or', re.IGNORECASE)


def fetch(offset):
    params = dict(dataset=DATASET, config='default', split='train',
                  offset=offset, length=BATCH)
    for attempt in range(8):
        try:
            response = requests.get(API, params=params, timeout=40)
            if response.status_code == 429:
                time.sleep(max(30, int(response.headers.get('Retry-After', '30'))))
                continue
            response.raise_for_status()
            return response.json()['rows']
        except (requests.RequestException, KeyError, ValueError):
            if attempt == 7:
                raise
            time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(f'Rate limited at offset {offset}')


def select(row):
    r = row['row']
    if r['source'] != 2:
        return None
    contest, index, rating = r['cf_contest_id'], r['cf_index'], r['cf_rating']
    if not (contest > 0 and re.fullmatch(r'[A-C][12]?', index or '')
            and 800 <= rating <= 1800):
        return None
    if r['input_file'] or r['output_file']:
        return None
    if r['time_limit'] and r['time_limit']['seconds'] > 5:
        return None
    desc = r['description'].strip()
    if len(desc) < 200 or EXCLUDE.search(desc):
        return None
    if len(r['private_tests']['input']) < 8 or not r['public_tests']['input']:
        return None
    raw = list(zip(r['public_tests']['input'], r['public_tests']['output']))
    private = list(zip(r['private_tests']['input'], r['private_tests']['output']))
    if len(private) > 14:
        stride = (len(private) - 1) / 13
        private = [private[round(i * stride)] for i in range(14)]
    raw += private
    seen = set()
    tests = []
    for inp, out in raw:
        if not (inp and out and len(inp.encode()) <= 128_000
                and len(out.encode()) <= 128_000):
            continue
        key = (inp, out)
        if key not in seen:
            seen.add(key)
            tests.append([inp, out])
    if len(tests) < 8:
        return None
    code = f'CF{contest}{index}'
    source = f'https://codeforces.com/problemset/problem/{contest}/{index}'
    return {
        'code': code, 'name': r['name'], 'source': source,
        'rating': rating, 'tags': r['cf_tags'] or [],
        'time_limit': min(5, max(1, r['time_limit']['seconds'] if r['time_limit'] else 2)),
        'memory_limit_bytes': r['memory_limit_bytes'],
        'description': desc,
        'tests': tests,
        'dataset_row': row['row_idx'],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=int, default=220)
    parser.add_argument('--max-offset', type=int, default=3000)
    parser.add_argument('--start-offset', type=int, default=0)
    parser.add_argument('--out', type=Path,
                        default=data_root() / 'problem-data' / 'imports' / 'codecontests_cf_candidates.jsonl')
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if args.out.exists():
        with args.out.open(encoding='utf-8') as handle:
            existing = {item['code']: item for line in handle if (item := json.loads(line))}
    print('existing candidates', len(existing), flush=True)
    start = args.start_offset
    while start < args.max_offset and len(existing) < args.target:
        offsets = list(range(start, min(start + BATCH * 2, args.max_offset), BATCH))
        with ThreadPoolExecutor(max_workers=2) as pool:
            pages = list(pool.map(fetch, offsets))
        for page in pages:
            for row in page:
                item = select(row)
                if item and item['code'] not in existing:
                    existing[item['code']] = item
                    if len(existing) >= args.target:
                        break
            if len(existing) >= args.target:
                break
        with args.out.open('w', encoding='utf-8') as handle:
            for item in existing.values():
                handle.write(json.dumps(item, ensure_ascii=False) + '\n')
        start += len(offsets) * BATCH
        print('scanned', start, 'candidates', len(existing), flush=True)
    print('result', len(existing), 'manifest', args.out, flush=True)


if __name__ == '__main__':
    main()
