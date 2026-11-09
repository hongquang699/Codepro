import os
import sys
import json
import re
import django
from bs4 import BeautifulSoup
from problem_data_path import data_root

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
django.setup()

from django.contrib.auth.models import User
from backend.judge.models import Problem, ProblemType, ProblemGroup, Profile

def convert_html_to_markdown(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted iframes or empty divs
    for iframe in soup.find_all('iframe'):
        iframe.decompose()
    
    for h4 in soup.find_all('h4'):
        text = h4.get_text().strip()
        h4.replace_with(f'\n\n### {text}\n\n')
        
    for h5 in soup.find_all('h5'):
        text = h5.get_text().strip()
        h5.replace_with(f'\n\n#### {text}\n\n')
        
    for pre in soup.find_all('pre'):
        code = pre.get_text().strip()
        pre.replace_with(f'\n```\n{code}\n```\n')
        
    for li in soup.find_all('li'):
        text = li.get_text().strip()
        li.replace_with(f'- {text}\n')
        
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        p.replace_with(f'{text}\n\n')
        
    for strong in soup.find_all('strong'):
        text = strong.get_text().strip()
        strong.replace_with(f'**{text}**')
        
    for em in soup.find_all('em'):
        text = em.get_text().strip()
        em.replace_with(f'*{text}*')

    res = soup.get_text()
    
    # Convert DMOJ math ~formula~ to MathJax $formula$
    res = re.sub(r'~([^~]+)~', r'$\1$', res)
    
    # Normalize multiple newlines
    res = re.sub(r'\n{3,}', '\n\n', res).strip()
    
    # Ensure it starts with ## Đề bài if not already
    if not res.startswith('##'):
        res = '## Đề bài\n\n' + res
        
    return res

def main():
    json_path = os.path.join(data_root(), 'problem-data', 'crawled', 'all_300_problems.json')
    if not os.path.exists(json_path):
        json_path = 'all_300_problems.json'

    with open(json_path, 'r', encoding='utf-8') as f:
        problems_data = json.load(f)

    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    author_profile = Profile.objects.filter(user=admin_user).first() if admin_user else None

    # Ensure ProblemGroup
    group_obj, _ = ProblemGroup.objects.get_or_create(
        name="01. Nhập môn",
        defaults={"full_name": "300 Bài Code Thiếu Nhi - Nhập Môn Lập Trình"}
    )

    # Cache for ProblemType
    type_cache = {}
    
    total_created = 0
    total_updated = 0

    for idx, p in enumerate(problems_data):
        code = p['code']
        name = p['name']
        raw_html = p['html']
        time_limit = float(p.get('time_limit', 1.0))
        memory_limit = int(p.get('memory_limit', 262144))
        points = float(p.get('points', 100.0))
        if points <= 0.001:
            points = 100.0  # normalize nominal point values

        code_num = int(code) if code.isdigit() else idx
        if code_num <= 80:
            difficulty = 'easy'
        elif code_num <= 220:
            difficulty = 'medium'
        else:
            difficulty = 'hard'

        md_statement = convert_html_to_markdown(raw_html)

        prob, created = Problem.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'description': md_statement,
                'time_limit': time_limit,
                'memory_limit': memory_limit,
                'points': points,
                'partial': False,
                'short_circuit': False,
                'is_public': True,
                'group': group_obj,
                'status': 'published',
                'difficulty': difficulty
            }
        )

        if author_profile:
            prob.authors.add(author_profile)

        # Associate types/tags
        for t_name in p.get('types', []):
            if t_name not in type_cache:
                t_obj, _ = ProblemType.objects.get_or_create(
                    name=t_name[:50],
                    defaults={"full_name": t_name[:100]}
                )
                type_cache[t_name] = t_obj
            prob.types.add(type_cache[t_name])

        if created:
            total_created += 1
        else:
            total_updated += 1

        if (idx + 1) % 50 == 0 or idx == len(problems_data) - 1:
            print(f"Processed {idx + 1}/{len(problems_data)} problems... (Created: {total_created}, Updated: {total_updated})")

    print(f"\nFinished importing! Total in database: {Problem.objects.count()} problems.")

if __name__ == '__main__':
    main()
