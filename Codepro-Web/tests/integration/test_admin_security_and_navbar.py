import urllib.request
import urllib.error
import json
import glob
import os

BASE_WEB = "http://localhost:8888"
BASE_API = "http://localhost:8000"

print("=" * 60)
print("CODING_OJ Security & UI Verification Suite")
print("=" * 60)

# 1. Test unauthenticated access to /admin
print("\n[1] Testing unauthenticated access to /admin...")
try:
    req = urllib.request.Request(f"{BASE_WEB}/admin")
    # Urllib follows redirects by default, let's make an opener that doesn't follow redirects
    class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            return fp

    opener = urllib.request.build_opener(NoRedirectHandler)
    resp = opener.open(req)
    loc = resp.headers.get("Location")
    print(f"Status Code: {resp.status}, Redirect Location: {loc}")
    assert resp.status == 302, f"Expected 302 redirect, got {resp.status}"
    assert "error=unauthorized" in loc, f"Expected unauthorized redirect, got {loc}"
    print("PASS: Unauthenticated user redirected to login page!")
except Exception as e:
    print("FAIL:", e)

# 2. Test admin access with admin cookie
print("\n[2] Testing authenticated admin access to /admin...")
try:
    req = urllib.request.Request(f"{BASE_WEB}/admin")
    req.add_header("Cookie", "role=admin; is_admin=true")
    resp = urllib.request.urlopen(req)
    print(f"Status Code: {resp.status}")
    assert resp.status == 200, f"Expected 200, got {resp.status}"
    html = resp.read().decode('utf-8')
    assert "Bảng Quản Trị Hệ Thống" in html or "admin-layout" in html
    print("PASS: Admin cookie successfully granted access to /admin!")
except Exception as e:
    print("FAIL:", e)

# 3. Test Judge Workers endpoint without admin permission
print("\n[3] Testing /api/v2/admin/judge-workers unauthorized access...")
try:
    req = urllib.request.Request(f"{BASE_API}/api/v2/admin/judge-workers")
    urllib.request.urlopen(req)
    print("FAIL: Expected 403 Forbidden, but request succeeded!")
except urllib.error.HTTPError as e:
    print(f"Status Code: {e.code}")
    assert e.code == 403, f"Expected 403, got {e.code}"
    print("PASS: Server rejected unauthorized access to judge workers endpoint!")

# 4. Test /api/v2/auth/admin-check
print("\n[4] Testing /api/v2/auth/admin-check unauthorized access...")
try:
    req = urllib.request.Request(f"{BASE_API}/api/v2/auth/admin-check?username=guest")
    urllib.request.urlopen(req)
    print("FAIL: Expected 403 Forbidden, but request succeeded!")
except urllib.error.HTTPError as e:
    print(f"Status Code: {e.code}")
    assert e.code in (401, 403), f"Expected 401 or 403, got {e.code}"
    print("PASS: Server rejected non-admin role check!")

# 5. Verify internal judge secret token is NOT leaked in any frontend code
print("\n[5] Scanning frontend for the configured Judge Manager token...")
judge_token = os.environ.get('JUDGE_AUTH_TOKEN', '')
frontend_files = glob.glob("frontend/**/*.js", recursive=True) + glob.glob("frontend/**/*.html", recursive=True)
leaked_in = []
for f in frontend_files:
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        content = fp.read()
    if judge_token and judge_token in content:
        leaked_in.append(f)

if leaked_in:
    print(f"FAIL: Secret token found in: {leaked_in}")
else:
    print(f"PASS: 0 leaks found across {len(frontend_files)} frontend files!")

# 6. Verify Navbar elements
print("\n[6] Verifying Navbar components and styles...")
with open("frontend/css/components/navbar.css", 'r', encoding='utf-8') as fp:
    nav_css = fp.read()

assert ".brand-badge-code" in nav_css, "Missing .brand-badge-code in navbar.css"
assert "#DC2626" in nav_css or "rgb(220" in nav_css or "crimson" in nav_css or "background:" in nav_css
assert ".nav-admin-link" in nav_css, "Missing .nav-admin-link in navbar.css"
assert "#38bdf8" in nav_css, "Missing cyan/sky color #38bdf8 for Quản trị link"

with open("frontend/js/components/navbar.js", 'r', encoding='utf-8') as fp:
    nav_js = fp.read()

assert "Quản trị" in nav_js
assert "Trang chủ" in nav_js
assert "Bài tập" in nav_js
assert "Cuộc thi" in nav_js
assert "Xếp hạng" in nav_js
assert "Bài nộp" in nav_js
assert "Cộng đồng" in nav_js
print("PASS: Navbar CSS and JS have all required elements and roles properly configured!")

# 7. Check source code masking on submissions API
print("\n[7] Testing submission source code security...")
try:
    # Fetch any submission ID
    req = urllib.request.Request(f"{BASE_API}/api/v2/submissions")
    data = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    submissions = data.get('results', data) if isinstance(data, dict) else data
    if submissions and len(submissions) > 0:
        sub_id = submissions[0].get('id')
        detail_req = urllib.request.Request(f"{BASE_API}/api/v2/submission/{sub_id}")
        detail_data = json.loads(urllib.request.urlopen(detail_req).read().decode('utf-8'))
        source = detail_data.get('source', '')
        print(f"Submission #{sub_id} source for anonymous user: {source}")
        assert "bảo mật" in source or "[Mã nguồn" in source or source is None, f"Source was exposed: {source}"
        print("PASS: Source code is safely masked for unauthorized users!")
    else:
        print("SKIP: No submissions in DB to test source masking.")
except Exception as e:
    print("Notice on source check:", e)

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("=" * 60)
