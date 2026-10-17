"""
CodeProOJ Problem Package Manager
Manages problem package directory in problem-data/problems/{CODE}/
Handles problem.yml, statements, testcases, checkers, validators, and solution testing
"""

import os
import zipfile
import io
import re
import json
from django.conf import settings
from security.encryption import file_cipher

def _safe_component(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', value) or '..' in value:
        raise ValueError('Tên file hoặc mã bài không hợp lệ')
    return value

def get_problem_dir(code):
    return os.path.join(settings.DMOJ_PROBLEM_DATA_ROOT, _safe_component(code))

def init_package(code, meta=None):
    base_dir = get_problem_dir(code)
    subdirs = ['statement', 'cases', 'validators', 'checkers', 'solutions', 'attachments']
    for s in subdirs:
        os.makedirs(os.path.join(base_dir, s), exist_ok=True)

    meta = meta or {}
    name = meta.get('name') or meta.get('title') or code
    time_limit = float(meta.get('time_limit') or 1.0)
    memory_limit = int(meta.get('memory_limit') or 256)
    points = float(meta.get('points') or 100.0)
    difficulty = meta.get('difficulty') or 'medium'
    status = meta.get('status') or 'draft'

    # Write problem.yml
    yml_path = os.path.join(base_dir, 'problem.yml')
    if not os.path.exists(yml_path):
        yml_content = f"""code: {code}
name: "{name}"
time_limit: {time_limit}
memory_limit: {memory_limit}
points: {points}
difficulty: {difficulty}
status: {status}
checker: standard
validator: standard
"""
        with open(yml_path, 'w', encoding='utf-8') as f:
            f.write(yml_content)

    # Write initial statement if missing
    md_path = os.path.join(base_dir, 'statement', 'statement.md')
    if not os.path.exists(md_path):
        sample_md = f"""# {name}

## Đề bài
Cho dữ liệu đầu vào. Hãy giải quyết bài toán theo đúng yêu cầu và in kết quả ra màn hình.

## Dữ liệu vào
Dòng đầu tiên chứa các số nguyên...

## Dữ liệu ra
In ra kết quả của bài toán.

## Ví dụ
### Input
```
2 3
```
### Output
```
5
```

## Giới hạn
- $1 \\le N \\le 10^5$
- Thời gian chạy: {time_limit}s
- Bộ nhớ: {memory_limit}MB
"""
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(sample_md)

    return base_dir

def get_statement(code):
    base_dir = get_problem_dir(code)
    md_path = os.path.join(base_dir, 'statement', 'statement.md')
    html_path = os.path.join(base_dir, 'statement', 'statement.html')

    markdown = ''
    html = ''
    if os.path.exists(md_path):
        with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
            markdown = f.read()
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

    return {
        'markdown': markdown,
        'html': html or markdown
    }

def save_statement(code, markdown_content, html_content=None):
    base_dir = get_problem_dir(code)
    stmt_dir = os.path.join(base_dir, 'statement')
    os.makedirs(stmt_dir, exist_ok=True)

    md_path = os.path.join(stmt_dir, 'statement.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    html_path = os.path.join(stmt_dir, 'statement.html')
    final_html = html_content or markdown_content
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(final_html)

    return True

def get_testcases(code):
    base_dir = get_problem_dir(code)
    cases_dir = os.path.join(base_dir, 'cases')
    if not os.path.exists(cases_dir):
        return []

    tests = []
    manifest = _read_testcase_manifest(base_dir)
    configured = {str(item.get('id')): item for item in manifest.get('cases', []) if isinstance(item, dict)}
    seen = set()
    for f in sorted(os.listdir(cases_dir)):
        if f.endswith('.in'):
            tid = f[:-3]
            seen.add(tid)

    ordered_ids = [str(item.get('id')) for item in manifest.get('cases', [])
                   if isinstance(item, dict) and str(item.get('id')) in seen]
    ordered_ids.extend(tid for tid in sorted(seen) if tid not in ordered_ids)
    for tid in ordered_ids:
        in_f = os.path.join(cases_dir, f"{tid}.in")
        out_f = os.path.join(cases_dir, f"{tid}.out")

        in_size = len(file_cipher.read_file(in_f)) if os.path.exists(in_f) else 0
        has_out = os.path.exists(out_f)
        out_size = len(file_cipher.read_file(out_f)) if has_out else 0

        # Sample snippet
        in_preview = ''
        out_preview = ''
        try:
            in_preview = file_cipher.read_file(in_f).decode('utf-8', errors='ignore')[:200]
            if has_out:
                out_preview = file_cipher.read_file(out_f).decode('utf-8', errors='ignore')[:200]
        except OSError:
            pass

        tests.append({
            'id': tid,
            'has_in': True,
            'has_out': has_out,
            'in_size': in_size,
            'out_size': out_size,
            'in_preview': in_preview,
            'out_preview': out_preview,
            'points': float(configured.get(tid, {}).get('points', 10)),
            'subtask': configured.get(tid, {}).get('subtask', 1),
            'sample': bool(configured.get(tid, {}).get('sample', False)),
        })

    return tests

def _read_testcase_manifest(base_dir):
    path = os.path.join(base_dir, 'testcases.json')
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {'cases': []}
    except (OSError, ValueError):
        return {'cases': []}

def _write_testcase_manifest(base_dir, manifest):
    path = os.path.join(base_dir, 'testcases.json')
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)

def has_subtasks(code):
    manifest = _read_testcase_manifest(get_problem_dir(code))
    if manifest.get('subtasks'):
        return True
    groups = {str(item.get('subtask', 1)) for item in manifest.get('cases', []) if isinstance(item, dict)}
    return len(groups) > 1

def save_testcase(code, tid, input_data, output_data, points=10, subtask=1, sample=False):
    tid = _safe_component(str(tid))
    base_dir = get_problem_dir(code)
    cases_dir = os.path.join(base_dir, 'cases')
    os.makedirs(cases_dir, exist_ok=True)

    in_path = os.path.join(cases_dir, f"{tid}.in")
    out_path = os.path.join(cases_dir, f"{tid}.out")

    file_cipher.write_file(in_path, input_data.encode('utf-8'))
    file_cipher.write_file(out_path, output_data.encode('utf-8'))

    manifest = _read_testcase_manifest(base_dir)
    cases = [item for item in manifest.get('cases', []) if str(item.get('id')) != tid]
    cases.append({'id': tid, 'points': float(points), 'subtask': int(subtask), 'sample': bool(sample)})
    manifest['cases'] = cases
    _write_testcase_manifest(base_dir, manifest)

    return True

def delete_testcase(code, tid):
    tid = _safe_component(str(tid))
    base_dir = get_problem_dir(code)
    cases_dir = os.path.join(base_dir, 'cases')
    in_path = os.path.join(cases_dir, f"{tid}.in")
    out_path = os.path.join(cases_dir, f"{tid}.out")

    deleted = False
    if os.path.exists(in_path):
        os.remove(in_path)
        deleted = True
    if os.path.exists(out_path):
        os.remove(out_path)
        deleted = True

    manifest = _read_testcase_manifest(base_dir)
    manifest['cases'] = [item for item in manifest.get('cases', []) if str(item.get('id')) != tid]
    _write_testcase_manifest(base_dir, manifest)

    return deleted

def import_zip_testcases(code, zip_file_bytes):
    if len(zip_file_bytes) > 20 * 1024 * 1024 or not zip_file_bytes.startswith(b'PK\x03\x04'):
        raise ValueError('Tệp ZIP không hợp lệ hoặc vượt giới hạn 20 MiB')
    base_dir = get_problem_dir(code)
    cases_dir = os.path.join(base_dir, 'cases')
    os.makedirs(cases_dir, exist_ok=True)

    imported_count = 0
    imported_ids = set()
    with zipfile.ZipFile(io.BytesIO(zip_file_bytes)) as zf:
        members = zf.infolist()
        if len(members) > 1000 or sum(item.file_size for item in members) > 100 * 1024 * 1024:
            raise ValueError('ZIP vượt giới hạn 1.000 file hoặc 100 MiB')
        target_names = set()
        for item in members:
            if item.is_dir() or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.(in|out|ans)', item.filename):
                raise ValueError('ZIP chỉ được chứa file testcase ở thư mục gốc')
            if item.flag_bits & 1 or item.file_size > 20 * 1024 * 1024:
                raise ValueError('Testcase trong ZIP không hợp lệ hoặc vượt giới hạn 20 MiB')
            target_name = item.filename[:-4] + '.out' if item.filename.endswith('.ans') else item.filename
            if target_name in target_names:
                raise ValueError('ZIP chứa testcase trùng tên')
            target_names.add(target_name)
        payloads = []
        for item in members:
            target_name = item.filename[:-4] + '.out' if item.filename.endswith('.ans') else item.filename
            payload = zf.read(item)
            if len(payload) != item.file_size:
                raise ValueError('Testcase trong ZIP không hợp lệ')
            payloads.append((target_name, payload))
        for target_name, payload in payloads:
            file_cipher.write_file(os.path.join(cases_dir, target_name), payload)
            imported_count += 1
            imported_ids.add(os.path.splitext(target_name)[0])

    manifest = _read_testcase_manifest(base_dir)
    existing = {str(item.get('id')): item for item in manifest.get('cases', []) if isinstance(item, dict)}
    for tid in sorted(imported_ids):
        existing.setdefault(tid, {'id': tid, 'points': 10, 'subtask': 1, 'sample': False})
    manifest['cases'] = sorted(existing.values(), key=lambda item: str(item.get('id')))
    _write_testcase_manifest(base_dir, manifest)

    return imported_count

def get_checker(code):
    base_dir = get_problem_dir(code)
    chk_dir = os.path.join(base_dir, 'checkers')
    for f in ['checker.cpp', 'checker.py', 'custom.cpp']:
        p = os.path.join(chk_dir, f)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8', errors='ignore') as fl:
                return {'type': 'custom', 'filename': f, 'code': fl.read()}
    return {'type': 'standard', 'filename': 'standard', 'code': '// Standard White-space Agnostic Checker\n'}

def save_checker(code, content, filename='checker.cpp'):
    filename = _safe_component(filename)
    if not filename.endswith(('.cpp', '.py')):
        raise ValueError('Tên checker không hợp lệ')
    base_dir = get_problem_dir(code)
    chk_dir = os.path.join(base_dir, 'checkers')
    os.makedirs(chk_dir, exist_ok=True)
    p = os.path.join(chk_dir, filename)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

def get_validator(code):
    base_dir = get_problem_dir(code)
    val_dir = os.path.join(base_dir, 'validators')
    for f in ['validator.cpp', 'validator.py']:
        p = os.path.join(val_dir, f)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8', errors='ignore') as fl:
                return {'type': 'custom', 'filename': f, 'code': fl.read()}
    return {'type': 'standard', 'filename': 'standard', 'code': '// Standard Non-empty Validator\n'}

def save_validator(code, content, filename='validator.cpp'):
    filename = _safe_component(filename)
    if not filename.endswith(('.cpp', '.py')):
        raise ValueError('Tên validator không hợp lệ')
    base_dir = get_problem_dir(code)
    val_dir = os.path.join(base_dir, 'validators')
    os.makedirs(val_dir, exist_ok=True)
    p = os.path.join(val_dir, filename)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

def get_solutions(code):
    base_dir = get_problem_dir(code)
    sol_dir = os.path.join(base_dir, 'solutions')
    if not os.path.exists(sol_dir):
        return []

    res = []
    for f in sorted(os.listdir(sol_dir)):
        if f.endswith(('.cpp', '.py', '.java', '.rs')):
            p = os.path.join(sol_dir, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fl:
                code_text = fl.read()
            res.append({
                'filename': f,
                'lang': 'cpp' if f.endswith('.cpp') else ('python' if f.endswith('.py') else 'java'),
                'code': code_text
            })
    return res

def save_solution(code, content, filename='official.py'):
    filename = _safe_component(filename)
    if not filename.endswith(('.cpp', '.py', '.java', '.rs')):
        raise ValueError('Tên solution không hợp lệ')
    base_dir = get_problem_dir(code)
    sol_dir = os.path.join(base_dir, 'solutions')
    os.makedirs(sol_dir, exist_ok=True)
    p = os.path.join(sol_dir, filename)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

def get_solution(code, filename='official.py'):
    filename = _safe_component(filename)
    base_dir = get_problem_dir(code)
    sol_path = os.path.join(base_dir, 'solutions', filename)
    if not os.path.exists(sol_path):
        # Check if cpp exists
        for alt in ['official.cpp', 'official.py', 'solution.cpp', 'solution.py']:
            alt_path = os.path.join(base_dir, 'solutions', alt)
            if os.path.exists(alt_path):
                sol_path = alt_path
                filename = alt
                break

    if not os.path.exists(sol_path):
        return None, None

    return filename, sol_path

def check_publish_readiness(code):
    stmt = get_statement(code)
    cases = get_testcases(code)
    solutions = get_solutions(code)

    has_stmt = len(stmt.get('markdown', '').strip()) > 30
    has_cases = len(cases) > 0
    has_sol = len(solutions) > 0

    checklist = [
        {'id': 'statement', 'name': 'Đề bài (Statement)', 'ok': has_stmt, 'desc': 'Đã có mô tả, input/output và ví dụ'},
        {'id': 'testcases', 'name': 'Bộ testcase (Cases)', 'ok': has_cases, 'desc': f'Có {len(cases)} testcase'},
        {'id': 'checker', 'name': 'Checker kiểm tra', 'ok': True, 'desc': 'Standard White-space agnostic checker'},
        {'id': 'solution', 'name': 'Solution mẫu (Official Solution)', 'ok': has_sol, 'desc': f'Đã upload {len(solutions)} solution'}
    ]

    ready = has_stmt and has_cases
    return {
        'ready': ready,
        'checklist': checklist
    }

def delete_package(code):
    base_dir = get_problem_dir(code)
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir, ignore_errors=True)
        return True
    return False
