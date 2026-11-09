"""Collect Codeforces tasks by reading CodeContests Parquet with DuckDB.

Requires duckdb and requests. Writes the same JSONL manifest as
collect_codecontests_cf.py; it does not modify the OJ database.
"""
import argparse
import json
from pathlib import Path

import duckdb
import requests

from collect_codecontests_cf import select
from problem_data_path import data_root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=int, default=230)
    parser.add_argument('--out', type=Path,
                        default=data_root() / 'problem-data' / 'imports' / 'codecontests_cf_candidates.jsonl')
    args = parser.parse_args()
    existing = {}
    if args.out.exists():
        with args.out.open(encoding='utf-8') as handle:
            existing = {item['code']: item for line in handle if (item := json.loads(line))}
    metadata = requests.get(
        'https://datasets-server.huggingface.co/parquet',
        params={'dataset': 'deepmind/code_contests'}, timeout=30
    ).json()
    urls = [entry['url'] for entry in metadata['parquet_files']
            if entry['split'] == 'train' and entry['config'] == 'default']
    if not urls:
        raise RuntimeError('No CodeContests training Parquet files')
    db = duckdb.connect()
    db.execute('INSTALL httpfs')
    db.execute('LOAD httpfs')
    db.execute('PRAGMA enable_progress_bar=false')
    fields = ('name, description, public_tests, private_tests, source, '
              'cf_contest_id, cf_index, cf_rating, cf_tags, time_limit, '
              'memory_limit_bytes, input_file, output_file')
    query = (f'SELECT {fields} FROM read_parquet(?) WHERE source=2 '
             'AND cf_rating BETWEEN 800 AND 1800 '
             "AND regexp_matches(cf_index, '^[A-C][12]?$')")
    result = db.execute(query, [urls])
    names = [column[0] for column in result.description]
    scanned = 0
    for values in result.fetchall():
        scanned += 1
        row = dict(zip(names, values))
        candidate = select({'row': row, 'row_idx': -1})
        if candidate and candidate['code'] not in existing:
            existing[candidate['code']] = candidate
        if scanned % 100 == 0:
            print('scanned', scanned, 'selected', len(existing), flush=True)
        if len(existing) >= args.target:
            break
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('w', encoding='utf-8') as handle:
        for candidate in existing.values():
            handle.write(json.dumps(candidate, ensure_ascii=False) + '\n')
    print('result', len(existing), 'from', scanned,
          'metadata matches; manifest', args.out, flush=True)


if __name__ == '__main__':
    main()
