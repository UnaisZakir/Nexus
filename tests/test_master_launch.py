import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database as db
from fastapi.testclient import TestClient
from main import app

def run_master_launch_tests():
    print("==================================================")
    print("  NEXUS ERP — MASTER LAUNCH SUITE VERIFICATION    ")
    print("==================================================")

    print("\n[1/5] Testing Database Engine & Schema Initialization...")
    db.init_db()
    print(" [PASS] Database engine & schema initialized.")

    client = TestClient(app)

    print("\n[2/5] Testing Multi-Step Business Onboarding Registration...")
    reg_res = client.post("/auth/register", data={
        "username": "test_corp_ceo",
        "email": "ceo@testcorp.com",
        "password": "password123",
        "role": "CEO",
        "plan": "corporate",
        "company": "Pak Tech Enterprises Ltd",
        "industry": "IT / Tech Services",
        "tax_id": "NTN-9988776-5",
        "business_type": "Private Limited",
        "annual_revenue": "Rs 10M - 50M",
        "currency": "PKR",
        "language": "ur"
    }, follow_redirects=False)

    assert reg_res.status_code == 303, f"Registration failed with status {reg_res.status_code}"
    user_cookie = reg_res.cookies.get("nexus_user")
    assert user_cookie is not None, "nexus_user cookie not returned upon registration"
    cookies_corp = {"nexus_user": user_cookie}
    print(" [PASS] Multi-Step Onboarding Registration -> Created 'Pak Tech Enterprises Ltd' (PKR, Urdu, Corporate)")

    print("\n[3/5] Testing Cash Flow Statement Analytics & Dashboard...")
    dash_res = client.get("/", cookies=cookies_corp)
    assert dash_res.status_code == 200, f"Dashboard returned status {dash_res.status_code}"
    assert "Statement of Cash Flows" in dash_res.text, "Cash Flow Statement section missing from Dashboard"
    print(" [PASS] Dashboard Cash Flow Statement (Operating, Investing, Financing) -> 200 OK")

    print("\n[4/5] Testing HR Custom Team Seats Manager (/team & /api/team/invite)...")
    team_page_res = client.get("/team", cookies=cookies_corp)
    assert team_page_res.status_code == 200, f"Team page status {team_page_res.status_code}"

    invite_res = client.post("/api/team/invite", data={
        "member_name": "Tariq Mahmood",
        "email": "tariq@testcorp.com",
        "role_title": "Senior Auditor",
        "permissions": "read_write"
    }, cookies=cookies_corp, follow_redirects=False)
    assert invite_res.status_code == 303, f"Team invite status {invite_res.status_code}"
    print(" [PASS] HR Custom Team Seats -> Invited 'Tariq Mahmood' (Senior Auditor) successfully")

    print("\n[5/5] Testing App Creator SuperAdmin Master Panel (/superadmin)...")
    # Login as Creator SuperAdmin (admin / admin123)
    admin_login_res = client.post("/auth/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
    assert admin_login_res.status_code == 303, f"SuperAdmin login status {admin_login_res.status_code}"
    cookies_admin = {"nexus_user": admin_login_res.cookies.get("nexus_user")}

    sa_res = client.get("/superadmin", cookies=cookies_admin)
    assert sa_res.status_code == 200, f"SuperAdmin panel status {sa_res.status_code}"
    assert "Tenant Privacy Guarantee Shield" in sa_res.text, "Privacy Shield notice missing from SuperAdmin panel"
    print(" [PASS] App Creator SuperAdmin Master Panel -> Accessed securely with Tenant Privacy Shield")

    print("\n==================================================")
    print(" [SUCCESS] LAUNCH READY! ALL MASTER LAUNCH TESTS PASSED 100%! ")
    print("==================================================")

if __name__ == "__main__":
    run_master_launch_tests()
