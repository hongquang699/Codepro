import sys, os, json
from bs4 import BeautifulSoup
from problem_data_path import data_root

crawled_dir = os.path.join(data_root(), 'problem-data', 'crawled')
in_path = os.path.join(crawled_dir, 'all_300_problems.json') if os.path.exists(os.path.join(crawled_dir, 'all_300_problems.json')) else 'all_300_problems.json'
out_path = os.path.join(crawled_dir, 'extracted_problems_all.json') if os.path.exists(crawled_dir) else 'extracted_problems_all.json'

with open(in_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

extracted = []
for p in data:
    soup = BeautifulSoup(p['html'], 'html.parser')
    pres = [pre.get_text().strip() for pre in soup.find_all('pre')]
    samples = []
    for i in range(0, len(pres), 2):
        if i + 1 < len(pres):
            samples.append({'in': pres[i], 'out': pres[i+1]})
    
    # Extract plain text
    full_text = soup.get_text('\n', strip=True)
    
    extracted.append({
        'code': p['code'],
        'name': p['name'],
        'group': p.get('group', ''),
        'types': p.get('types', []),
        'text': full_text,
        'samples': samples
    })

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(extracted, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(extracted)} problems successfully to {out_path}.")
