import sys, os, json
from bs4 import BeautifulSoup
from problem_data_path import data_root

sys.stdout.reconfigure(encoding='utf-8')

file_path = os.path.join(data_root(), 'problem-data', 'crawled', 'all_300_problems.json')
if not os.path.exists(file_path):
    file_path = 'all_300_problems.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for p in data[:30]:
    soup = BeautifulSoup(p['html'], 'html.parser')
    desc = soup.get_text(' ', strip=True)
    print(f"[{p['code']}] {p['name']}: {desc[:100]}...")
