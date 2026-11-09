import json
import urllib.request
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8888"

def test_full_pipeline():
    print("=== Testing Submissions Subsystem on Port 8888 ===")

    # 1. Test POST Submit
    submit_url = f"{BASE_URL}/api/v1/submissions/submit/"
    sample_code = """#include <iostream>
using namespace std;

int main() {
    int a, b;
    if (cin >> a >> b) {
        cout << a + b << endl;
    }
    return 0;
}
"""
    payload = {
        "problem": "SUMA",
        "language": "CPP17",
        "source_code": sample_code
    }
    req = urllib.request.Request(
        submit_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201, f"Expected 201, got {resp.status}"
        data = json.loads(resp.read().decode('utf-8'))
        print(f"[OK] POST /api/v1/submissions/submit/ returned: {data}")
        submission_id = data["submission_id"]
        assert submission_id > 0, "Invalid submission ID"

    # 2. Test GET Submission Detail
    detail_url = f"{BASE_URL}/api/v1/submissions/{submission_id}/"
    with urllib.request.urlopen(detail_url) as resp:
        assert resp.status == 200
        detail = json.loads(resp.read().decode('utf-8'))
        print(f"[OK] GET /api/v1/submissions/{submission_id}/ -> Problem: {detail['problem']}, Verdict: {detail['verdict']}, Score: {detail['score']}")
        prob_code = detail["problem"]["code"] if isinstance(detail["problem"], dict) else detail["problem"]
        assert prob_code == "SUMA"
        assert "source_code" in detail

    # 3. Test GET Testcases & Verify Hidden Input Masking
    tc_url = f"{BASE_URL}/api/v1/submissions/{submission_id}/testcases/"
    with urllib.request.urlopen(tc_url) as resp:
        assert resp.status == 200
        tc_data = json.loads(resp.read().decode('utf-8'))
        testcases = tc_data.get("testcases", [])
        print(f"[OK] GET /api/v1/submissions/{submission_id}/testcases/ returned {len(testcases)} testcases")
        for tc in testcases:
            if tc.get("is_hidden"):
                assert tc.get("input") == "", "SECURITY VIOLATION: Hidden testcase input was exposed to client!"

    # 4. Test Rejudge API
    rejudge_url = f"{BASE_URL}/api/v1/submissions/{submission_id}/rejudge/"
    r_req = urllib.request.Request(rejudge_url, data=b"{}", headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(r_req) as resp:
        assert resp.status == 200
        r_data = json.loads(resp.read().decode('utf-8'))
        print(f"[OK] POST /api/v1/submissions/{submission_id}/rejudge/ -> {r_data}")
        assert r_data["success"] is True

    # 5. Test Submissions List with Filter
    list_url = f"{BASE_URL}/api/v1/submissions/?problem=SUMA&language=CPP17"
    with urllib.request.urlopen(list_url) as resp:
        assert resp.status == 200
        list_data = json.loads(resp.read().decode('utf-8'))
        print(f"[OK] GET /api/v1/submissions/?problem=SUMA -> Total: {list_data['total']}, Items in page: {len(list_data['items'])}")
        assert list_data["total"] >= 1

    print("\n>>> ALL SUBMISSIONS SUBSYSTEM TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_full_pipeline()
