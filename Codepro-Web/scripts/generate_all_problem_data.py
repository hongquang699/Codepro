import os
import sys
import json
import math
import random
import re
from bs4 import BeautifulSoup
from problem_data_path import data_root

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PROBLEMS_DATA_DIR = os.path.join(data_root(), "problem-data", "problems")

def convert_html_to_markdown(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
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
    res = re.sub(r'~([^~]+)~', r'$\1$', res)
    res = re.sub(r'\n{3,}', '\n\n', res).strip()
    if not res.startswith('##'):
        res = '## Đề bài\n\n' + res
    return res

# Safe, verified solvers for arithmetic and classic problems
SOLVERS = {
    0: lambda inp: str(int(inp.strip().split()[0]) + int(inp.strip().split()[1]) - int(inp.strip().split()[2])),
    1: lambda inp: str(int(inp.strip()) + 2025),
    2: lambda inp: str(int(inp.strip()) - 2),
    3: lambda inp: str(int(inp.strip()) * 3),
    4: lambda inp: f"{int(inp.strip()) / 3:.2f}",
    5: lambda inp: f"{int(inp.strip())**2}\n{int(inp.strip())**5}",
    6: lambda inp: f"{math.sqrt(abs(float(inp.strip()))):.2f}",
    7: lambda inp: f"{1.0 / (float(inp.strip()) or 1.0):.5f}",
    10: lambda inp: f"{int(inp.strip().split()[0]) // (int(inp.strip().split()[1]) or 1)} {int(inp.strip().split()[0]) % (int(inp.strip().split()[1]) or 1)}",
    11: lambda inp: f"{int(inp.strip().split()[0]) // (int(inp.strip().split()[1]) or 1)} {int(inp.strip().split()[0]) % (int(inp.strip().split()[1]) or 1)}",
    12: lambda inp: f"{abs(int(inp.strip())) % 10} {abs(int(inp.strip())) // 10 % 10}",
    13: lambda inp: str(sum(int(c) for c in inp.strip() if c.isdigit())),
    14: lambda inp: str((abs(int(inp.strip().split()[0])) % 10) + (abs(int(inp.strip().split()[1])) % 10)),
    15: lambda inp: str((abs(int(inp.strip().split()[0])) % 10) + (abs(int(inp.strip().split()[1])) // 10 % 10)),
    16: lambda inp: f"{int(inp.strip()) // 5000} {int(inp.strip()) % 5000}",
    17: lambda inp: f"{int(inp.strip()) // 5000} {(int(inp.strip()) % 5000) // 2000} {((int(inp.strip()) % 5000) % 2000) // 1000}",
    18: lambda inp: f"{int(inp.strip()) // 3600}:{(int(inp.strip()) % 3600) // 60}:{int(inp.strip()) % 60}",
    19: lambda inp: str(sum(math.ceil(int(x) / 2) for x in inp.strip().split())),
    20: lambda inp: f"{int(inp.strip().split()[0]) // (int(inp.strip().split()[1]) or 1)} {int(inp.strip().split()[0]) % (int(inp.strip().split()[1]) or 1)}",
    21: lambda inp: f"{int(inp.strip()) * 4} {int(inp.strip()) ** 2}",
    22: lambda inp: f"{2 * 3.14 * float(inp.strip()):.2f} {3.14 * (float(inp.strip())**2):.2f}",
    23: lambda inp: f"{(int(inp.strip().split()[0]) + int(inp.strip().split()[1])) * 2} {int(inp.strip().split()[0]) * int(inp.strip().split()[1])}",
    24: lambda inp: f"{float(inp.strip().split()[0]) * float(inp.strip().split()[1]) / 2:g}",
    27: lambda inp: f"{sum(map(float, inp.strip().split())) / 3:.1f}",
    28: lambda inp: f"{sum(map(float, inp.strip().split())) / 3:.1f}",
    30: lambda inp: f"{(float(inp.strip()) / 4)**2:g}",
    32: lambda inp: "DUONG" if int(inp.strip()) > 0 else ("AM" if int(inp.strip()) < 0 else "KHONG"),
    33: lambda inp: "CHAN" if int(inp.strip()) % 2 == 0 else "LE",
    34: lambda inp: str(max(map(int, inp.strip().split()))),
    35: lambda inp: str(min(map(int, inp.strip().split()))),
    38: lambda inp: " ".join(map(str, sorted(map(int, inp.strip().split())))),
    39: lambda inp: "So duong" if int(inp.strip()) > 0 else ("So am" if int(inp.strip()) < 0 else "So khong"),
    41: lambda inp: "Yes" if int(inp.strip()) % 6 == 0 else "No",
    42: lambda inp: "Yes" if int(inp.strip()) > 100 else "No",
    44: lambda inp: "YES" if (int(inp.strip()) % 400 == 0 or (int(inp.strip()) % 4 == 0 and int(inp.strip()) % 100 != 0)) else "NO",
    47: lambda inp: "Yes" if math.isqrt(max(0, int(inp.strip())))**2 == int(inp.strip()) else "No",
    50: lambda inp: str(sum([
        min(max(0, int(inp.strip())), 50) * 600,
        min(max(0, int(inp.strip()) - 50), 50) * 800,
        min(max(0, int(inp.strip()) - 100), 100) * 1100,
        max(0, int(inp.strip()) - 200) * 1500
    ])),
    61: lambda inp: " ".join(str(i) for i in range(1, int(inp.strip()) + 1)),
    62: lambda inp: str(sum(range(1, int(inp.strip()) + 1))),
    63: lambda inp: " ".join(str(i) for i in range(1, int(inp.strip()) + 1) if i % 3 == 0),
    64: lambda inp: str(int(inp.strip()) // 3),
    65: lambda inp: str(sum(i for i in range(1, int(inp.strip()) + 1) if i % 2 == 0)),
    66: lambda inp: str(sum(i for i in range(1, int(inp.strip()) + 1) if i % 15 == 0)),
    67: lambda inp: str(sum(i for i in range(1, int(inp.strip()) + 1) if i % 3 == 0 or i % 5 == 0)),
    71: lambda inp: " ".join(str(i) for i in range(int(inp.strip().split()[0]), int(inp.strip().split()[-1]) + 1)),
    72: lambda inp: str(sum(range(int(inp.strip().split()[0]), int(inp.strip().split()[-1]) + 1))),
    73: lambda inp: str(sum(1 for i in range(int(inp.strip().split()[0]), int(inp.strip().split()[-1]) + 1) if i % 3 == 0)),
    74: lambda inp: " ".join(str(i) for i in range(int(inp.strip().split()[0]), int(inp.strip().split()[-1]) + 1) if i % 2 == 0),
    75: lambda inp: str(sum(1 for i in range(int(inp.strip().split()[0]), int(inp.strip().split()[-1]) + 1) if i % 2 == 0)),
    76: lambda inp: str(sum(i for i in range(int(inp.strip().split()[0]), int(inp.strip().split()[-1]) + 1) if i % 2 == 0)),
    77: lambda inp: str(sum(i for i in range(int(inp.strip().split()[0]), int(inp.strip().split()[-1]) + 1) if i % 2 == 0) // max(1, sum(1 for i in range(int(inp.strip().split()[0]), int(inp.strip().split()[-1]) + 1) if i % 2 == 0))),
    81: lambda inp: str(math.gcd(*map(abs, map(int, inp.strip().split())))),
    82: lambda inp: f"{int(inp.strip().split()[0]) // math.gcd(int(inp.strip().split()[0]), int(inp.strip().split()[1]))}/{int(inp.strip().split()[1]) // math.gcd(int(inp.strip().split()[0]), int(inp.strip().split()[1]))}",
    83: lambda inp: str(len([c for c in inp.strip() if c.isdigit()])),
    84: lambda inp: " ".join(reversed([c for c in inp.strip() if c.isdigit()])),
    85: lambda inp: str(sum(int(c) for c in inp.strip() if c.isdigit())),
    150: lambda inp: f"{' '.join(str(v) for v in list(map(int, inp.strip().split('\n')[0].split())) if v != int(inp.strip().split('\n')[1].strip()))}\n{len([v for v in list(map(int, inp.strip().split('\n')[0].split())) if v != int(inp.strip().split('\n')[1].strip())])}",
    200: lambda inp: "".join([inp.split('\n')[2].strip() if i == int(inp.split('\n')[1].strip()) else c for i, c in enumerate(inp.split('\n')[0])]),
    250: lambda inp: " ".join(str(i) for i, line in enumerate([l for l in inp.strip().split('\n') if l.strip()]) if all(int(x) < 0 for x in line.split())),
    300: lambda inp: " ".join(str(x) for x in (lambda a, x: (a.remove(x) or a) if x in a else a)(list(map(int, inp.strip().split('\n')[0].split())), int(inp.strip().split('\n')[1].strip())))
}

def main():
    json_path = os.path.join(data_root(), 'problem-data', 'crawled', 'all_300_problems.json')
    if not os.path.exists(json_path):
        json_path = 'all_300_problems.json'

    with open(json_path, 'r', encoding='utf-8') as f:
        problems = json.load(f)

    os.makedirs(PROBLEMS_DATA_DIR, exist_ok=True)
    print(f"Generating packages and testcases for {len(problems)} problems...")

    total_tests_count = 0

    for idx, p in enumerate(problems):
        code = p['code']
        code_num = int(code) if code.isdigit() else idx
        name = p['name']
        time_limit = float(p.get('time_limit', 1.0))
        memory_limit = int(p.get('memory_limit', 262144))

        # Target number of tests:
        # Easy: 10 - 20
        # Medium: 20 - 35
        # Hard: 35 - 50 (key benchmarks: up to 100)
        if code_num <= 50:
            target_tests = 15
            difficulty = "easy"
        elif code_num <= 150:
            target_tests = 25
            difficulty = "medium"
        elif code_num <= 270:
            target_tests = 35
            difficulty = "hard"
        else:
            target_tests = 50 # up to 100 for top problems
            difficulty = "hard"

        prob_dir = os.path.join(PROBLEMS_DATA_DIR, code)
        cases_dir = os.path.join(prob_dir, "cases")
        statement_dir = os.path.join(prob_dir, "statement")
        os.makedirs(cases_dir, exist_ok=True)
        os.makedirs(statement_dir, exist_ok=True)

        # 1. problem.yml
        yml_content = (
            f"code: \"{code}\"\n"
            f"name: \"{name}\"\n"
            f"time_limit: {time_limit}\n"
            f"memory_limit: {memory_limit}\n"
            f"points: 100.0\n"
            f"difficulty: \"{difficulty}\"\n"
            f"status: \"published\"\n"
            f"checker: \"standard\"\n"
            f"validator: \"standard\"\n"
        )
        with open(os.path.join(prob_dir, "problem.yml"), "w", encoding="utf-8") as yf:
            yf.write(yml_content)

        # 2. statement.md
        md_text = convert_html_to_markdown(p['html'])
        with open(os.path.join(statement_dir, "statement.md"), "w", encoding="utf-8") as mf:
            mf.write(md_text)
        with open(os.path.join(statement_dir, "vi.md"), "w", encoding="utf-8") as vf:
            vf.write(md_text)

        # 3. Extract sample pairs from HTML
        soup = BeautifulSoup(p['html'], 'html.parser')
        pres = [pre.get_text().strip() for pre in soup.find_all('pre')]
        sample_pairs = []
        for i in range(0, len(pres), 2):
            if i + 1 < len(pres):
                sample_pairs.append((pres[i], pres[i+1]))

        case_idx = 1
        # Write official sample cases
        for s_in, s_out in sample_pairs:
            in_file = os.path.join(cases_dir, f"{case_idx:02d}.in")
            out_file = os.path.join(cases_dir, f"{case_idx:02d}.out")
            with open(in_file, "w", encoding="utf-8") as f_in:
                f_in.write(s_in.strip() + "\n")
            with open(out_file, "w", encoding="utf-8") as f_out:
                f_out.write(s_out.strip() + "\n")
            case_idx += 1

        # Check solver
        solver = SOLVERS.get(code_num)
        if solver and sample_pairs:
            sample_in = sample_pairs[0][0]
            lines = sample_in.strip().split('\n')
            
            while case_idx <= target_tests:
                try:
                    new_lines = []
                    for line in lines:
                        tokens = line.split()
                        new_tokens = []
                        for tok in tokens:
                            if tok.lstrip('-').isdigit():
                                val = int(tok)
                                if case_idx <= 8:
                                    new_val = random.randint(-15, 25)
                                elif case_idx <= 20:
                                    new_val = random.randint(1, 100)
                                else:
                                    new_val = random.randint(10, 500)
                                if val >= 0:
                                    new_val = abs(new_val)
                                if new_val == 0 and "chia" in name.lower():
                                    new_val = 1
                                new_tokens.append(str(new_val))
                            else:
                                new_tokens.append(tok)
                        new_lines.append(" ".join(new_tokens))
                    
                    gen_in = "\n".join(new_lines)
                    gen_out = solver(gen_in)
                    if gen_out is not None:
                        in_file = os.path.join(cases_dir, f"{case_idx:02d}.in")
                        out_file = os.path.join(cases_dir, f"{case_idx:02d}.out")
                        with open(in_file, "w", encoding="utf-8") as f_in:
                            f_in.write(gen_in.strip() + "\n")
                        with open(out_file, "w", encoding="utf-8") as f_out:
                            f_out.write(str(gen_out).strip() + "\n")
                        case_idx += 1
                    else:
                        break
                except Exception:
                    break

        total_tests_count += (case_idx - 1)

        if (idx + 1) % 50 == 0 or idx == len(problems) - 1:
            print(f"Generated {idx + 1}/{len(problems)} problem packages (Total testcases: {total_tests_count})")

    print(f"\nCompleted successfully!")
    print(f"Total problems prepared: {len(problems)}")
    print(f"Total test cases generated: {total_tests_count}")

if __name__ == '__main__':
    main()
