import os
import zipfile
import shutil
from django.conf import settings
from backend.judge.models import Problem, ContestProblem
from backend.judge.problem_package import _safe_component

def get_contest_storage_dir(contest_key):
    path = os.path.join(settings.CODEPRO_CONTEST_PACKAGE_ROOT, _safe_component(contest_key))
    os.makedirs(path, exist_ok=True)
    return path

def get_problem_storage_dir(contest_key, prefix):
    path = os.path.join(get_contest_storage_dir(contest_key), 'problems', _safe_component(prefix))
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, 'tests'), exist_ok=True)
    os.makedirs(os.path.join(path, 'checker'), exist_ok=True)
    os.makedirs(os.path.join(path, 'validator'), exist_ok=True)
    os.makedirs(os.path.join(path, 'solutions'), exist_ok=True)
    return path

def sync_problem_to_contest_storage(contest, contest_problem):
    """Sync statement and problem definition to storage/contests/<key>/problems/<prefix>."""
    prob = contest_problem.problem
    prefix = contest_problem.output_prefix or 'A'
    pdir = get_problem_storage_dir(contest.key, prefix)

    # Write problem.yml
    yml_path = os.path.join(pdir, 'problem.yml')
    with open(yml_path, 'w', encoding='utf-8') as f:
        f.write(f"code: '{prob.code}'\n")
        f.write(f"name: '{prob.name}'\n")
        f.write(f"prefix: '{prefix}'\n")
        f.write(f"points: {contest_problem.points}\n")
        f.write(f"time_limit: {prob.time_limit}\n")
        f.write(f"memory_limit: {prob.memory_limit}\n")
        f.write(f"difficulty: '{prob.difficulty}'\n")

    # Write statement.md
    stmt_path = os.path.join(pdir, 'statement.md')
    with open(stmt_path, 'w', encoding='utf-8') as f:
        f.write(prob.description or '')

    # Copy testcases from DMOJ_PROBLEM_DATA_ROOT if exists
    dmoj_cases = os.path.join(settings.DMOJ_PROBLEM_DATA_ROOT, prob.code, 'cases')
    tests_dir = os.path.join(pdir, 'tests')
    if os.path.isdir(dmoj_cases):
        for fname in os.listdir(dmoj_cases):
            src = os.path.join(dmoj_cases, fname)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(tests_dir, fname))

    return pdir
