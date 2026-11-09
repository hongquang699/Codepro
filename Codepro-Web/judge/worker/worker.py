"""
CodeProOJ Standalone Judge Worker Daemon
Connects to Django Backend via API & Heartbeat
Monitors Queued Submissions and Executes Grading
"""

import os
import time
import json
from urllib import request

API_URL = os.getenv('CODEPROOJ_API_URL', 'http://127.0.0.1:8000/api/v2')
JUDGE_NAME = os.getenv('JUDGE_NAME', 'codeprooj-judge-01')
JUDGE_AUTH_TOKEN = os.getenv('JUDGE_AUTH_TOKEN', '')

def send_heartbeat():
    if not JUDGE_AUTH_TOKEN:
        print('[JUDGE WORKER] JUDGE_AUTH_TOKEN is required for heartbeat')
        return False
    try:
        payload = json.dumps({
            'name': JUDGE_NAME,
            'load': 0.12,
            'ping': 0.45,
            'runtimes': {
                'gcc': '11.2 (GNU C++)',
                'python': '3.12 (CPython)',
                'rust': '1.75'
            }
        }).encode('utf-8')

        req = request.Request(
            f"{API_URL}/judge/heartbeat",
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {JUDGE_AUTH_TOKEN}',
            }
        )
        with request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[JUDGE WORKER] Heartbeat error: {e}")
        return False

def check_and_grade_submissions():
    # If running with access to Django environment, process queued submissions
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
        if not django.apps.apps.ready:
            django.setup()

        from backend.judge.models import Submission
        from backend.judge.bridge import grade_submission

        queued_subs = Submission.objects.filter(status='QU').order_by('id')[:5]
        for sub in queued_subs:
            print(f"[JUDGE WORKER] Processing queued submission #{sub.id} ({sub.problem.code})...")
            grade_submission(sub.id)
            print(f"[JUDGE WORKER] Submission #{sub.id} completed with verdict: {sub.result}")
    except Exception as e:
        # Django setup optional if operating purely via REST
        pass

def main():
    print(f"==================================================")
    print(f" [CODEPROOJ JUDGE DAEMON] {JUDGE_NAME} Active")
    print(f" API Base: {API_URL}")
    print(f"==================================================")

    # Initial heartbeat
    send_heartbeat()

    while True:
        try:
            send_heartbeat()
            check_and_grade_submissions()
        except KeyboardInterrupt:
            print("[JUDGE WORKER] Stopping daemon.")
            break
        except Exception as e:
            print(f"[JUDGE WORKER] Loop exception: {e}")

        time.sleep(10)

if __name__ == '__main__':
    main()
