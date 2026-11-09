import sys, os, json
from bs4 import BeautifulSoup
from problem_data_path import data_root

sys.stdout.reconfigure(encoding='utf-8')

crawled_dir = os.path.join(data_root(), 'problem-data', 'crawled')
in_path = os.path.join(crawled_dir, 'all_300_problems.json') if os.path.exists(os.path.join(crawled_dir, 'all_300_problems.json')) else 'all_300_problems.json'
out_path = os.path.join(crawled_dir, 'problems_summary.json') if os.path.exists(crawled_dir) else 'problems_summary.json'

with open(in_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total problems loaded: {len(data)}")

summary = []
for p in data:
    soup = BeautifulSoup(p['html'], 'html.parser')
    pres = [pre.get_text().strip() for pre in soup.find_all('pre')]
    
    samples = []
    for i in range(0, len(pres), 2):
        if i + 1 < len(pres):
            samples.append({'in': pres[i], 'out': pres[i+1]})
    
    summary.append({
        'code': p['code'],
        'name': p['name'],
        'group': p.get('group', ''),
        'types': p.get('types', []),
        'time_limit': p.get('time_limit', 1.0),
        'memory_limit': p.get('memory_limit', 262144),
        'sample_count': len(samples),
        'samples': samples
    })

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"Saved {out_path} with {len(summary)} items")
