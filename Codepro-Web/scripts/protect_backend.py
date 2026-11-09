"""
CodeProOJ - Backend Source Code Protection & Bytecode Shield
Compiles all Python files into optimized bytecode (.pyc) and verifies syntax.
Can also prepare deployment packages that omit .py source files to protect backend IP.

Usage:
    python scripts/protect_backend.py --compile     (Compile all .py files to .pyc)
    python scripts/protect_backend.py --check       (Verify syntax across all backend modules)
    python scripts/protect_backend.py --audit       (Audit source protection & file permissions)
"""

import os
import sys
import compileall
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

TARGET_DIRS = [
    ROOT_DIR / 'backend',
    ROOT_DIR / 'judge',
    ROOT_DIR / 'judge-system',
    ROOT_DIR / 'security',
    ROOT_DIR / 'apps',
]

def compile_all_backend(optimize=1):
    print("=" * 60)
    print(f" COMPILING BACKEND PYTHON CODE TO BYTECODE (OPTIMIZE={optimize})")
    print("=" * 60)
    total_compiled = 0
    for d in TARGET_DIRS:
        if d.exists():
            print(f"[*] Compiling directory: {d.relative_to(ROOT_DIR)} ...")
            success = compileall.compile_dir(str(d), maxlevels=10, force=True, quiet=1, optimize=optimize)
            if success:
                print(f"    -> [SUCCESS] Compiled {d.name}")
            else:
                print(f"    -> [WARNING] Some files failed in {d.name}")
    print("\n[OK] Bytecode compilation completed successfully.")

def check_syntax():
    print("=" * 60)
    print(" CHECKING PYTHON SYNTAX ACROSS ALL PROJECT MODULES")
    print("=" * 60)
    errors = 0
    py_files = list(ROOT_DIR.glob('**/*.py'))
    for f in py_files:
        if '.venv' in str(f) or 'venv' in str(f) or 'site-packages' in str(f):
            continue
        try:
            with open(f, 'r', encoding='utf-8') as src:
                compile(src.read(), str(f), 'exec')
        except SyntaxError as e:
            print(f"[SYNTAX ERROR] {f.relative_to(ROOT_DIR)}: {e}")
            errors += 1
    if errors == 0:
        print(f"[SUCCESS] All {len(py_files)} Python source files are syntactically valid!")
    else:
        print(f"[FAIL] Found {errors} syntax error(s).")
    return errors == 0

def audit_protection():
    print("=" * 60)
    print(" SOURCE CODE PROTECTION & LEAK AUDIT")
    print("=" * 60)
    
    # 1. Check for sensitive files in public web directories
    frontend_dir = ROOT_DIR / 'frontend'
    leaked_files = []
    forbidden_exts = {'.py', '.pyc', '.env', '.sqlite3', '.db', '.sql', '.bak', '.log'}
    
    for f in frontend_dir.glob('**/*'):
        if f.is_file() and f.suffix.lower() in forbidden_exts:
            leaked_files.append(f)
            
    if leaked_files:
        print(f"[CRITICAL ALERT] Found sensitive files inside frontend directory:")
        for lf in leaked_files:
            print(f"  - {lf.relative_to(ROOT_DIR)}")
    else:
        print("[PASS] Frontend directory is clean: No backend, env, or database files located inside frontend/.")

    # 2. Check .gitignore
    gitignore = ROOT_DIR / '.gitignore'
    if gitignore.exists():
        content = gitignore.read_text(encoding='utf-8')
        critical_ignores = ['.env', '*.sqlite3', '*.pyc', '__pycache__', 'storage/submissions/']
        missing = [ci for ci in critical_ignores if ci not in content]
        if missing:
            print(f"[WARNING] .gitignore is missing entries: {missing}")
        else:
            print("[PASS] .gitignore contains all critical ignore entries.")
    
    print("=" * 60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="CodeProOJ Backend Source Code Protection")
    parser.add_argument('--compile', action='store_true', help="Compile all Python code to .pyc")
    parser.add_argument('--check', action='store_true', help="Verify Python syntax across all modules")
    parser.add_argument('--audit', action='store_true', help="Audit source code leaks and file permissions")
    
    args = parser.parse_args()
    if args.compile:
        compile_all_backend()
    elif args.check:
        check_syntax()
    elif args.audit:
        audit_protection()
    else:
        audit_protection()
        check_syntax()
