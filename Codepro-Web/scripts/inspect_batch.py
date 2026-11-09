import sys, os, json
from problem_data_path import data_root

sys.stdout.reconfigure(encoding='utf-8')

summary_path = os.path.join(data_root(), 'problem-data', 'crawled', 'problems_summary.json')
if not os.path.exists(summary_path):
    summary_path = 'problems_summary.json'

with open(summary_path, 'r', encoding='utf-8') as f:
    s = json.load(f)

p_map = {x['code']: x for x in s}

start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
end = int(sys.argv[2]) if len(sys.argv) > 2 else 10

for code_num in range(start, end + 1):
    code = f"{code_num:03d}"
    if code in p_map:
        p = p_map[code]
        print(f"=== [{code}] {p['name']} ===")
        for i, sample in enumerate(p['samples']):
            print(f"  Sample {i+1} In:  {repr(sample['in'])}")
            print(f"  Sample {i+1} Out: {repr(sample['out'])}")
