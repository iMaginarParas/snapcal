import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("=== Testing Admin Platform Backend APIs ===")

    # 1. Ecosystem health
    res = client.get("/api/admin/ecosystem/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health_data = res.json()
    assert health_data.get("success") is True
    print("[PASS] Ecosystem Health API")

    # 2. Coaches Overview
    res = client.get("/api/admin/coaches")
    assert res.status_code == 200, f"Get coaches failed: {res.text}"
    coaches_data = res.json()
    assert coaches_data.get("success") is True
    assert len(coaches_data.get("data", [])) > 0
    test_coach_id = coaches_data["data"][0]["id"]
    print(f"[PASS] Get Coaches API ({len(coaches_data['data'])} coaches found)")

    # 3. Coach Deep Dive
    res = client.get(f"/api/admin/coaches/{test_coach_id}/deep-dive")
    assert res.status_code == 200, f"Deep dive failed: {res.text}"
    deep_dive = res.json()
    assert deep_dive.get("success") is True
    assert "financials" in deep_dive
    assert "clients" in deep_dive
    print("[PASS] Coach 360 Deep-Dive Inspector API")

    # 4. Provision Coach
    new_email = "test.provision@sabcoach.com"
    res = client.post("/api/admin/coaches", json={
        "name": "Test Provision Coach",
        "email": new_email,
        "password": "TempPass123!@",
        "role": "Mobility & Performance Coach",
        "practiceName": "Precision Test Studio"
    })
    assert res.status_code == 200, f"Provision coach failed: {res.text}"
    prov_data = res.json()
    assert prov_data.get("success") is True
    new_cid = prov_data["coach"]["id"]
    print(f"[PASS] Coach Provisioning API (Created ID: {new_cid})")

    # 5. Update Coach Profile
    res = client.put(f"/api/admin/coaches/{new_cid}", json={
        "bio": "Updated bio via automated admin test suite.",
        "phone": "+91 98888 77777"
    })
    assert res.status_code == 200
    print("[PASS] Update Coach API")

    # 6. Reset Password
    res = client.post(f"/api/admin/coaches/{new_cid}/reset-password", json={
        "tempPassword": "BrandNewPassword123!"
    })
    assert res.status_code == 200
    print("[PASS] Reset Coach Password API")

    # 7. Delete Coach
    res = client.delete(f"/api/admin/coaches/{new_cid}")
    assert res.status_code == 200
    print("[PASS] Delete Coach API")

    # 8. SabTrack Mobile Users / CRM Directory
    res = client.get("/api/admin/sabtrack/users")
    assert res.status_code == 200, f"Get users failed: {res.text}"
    users_data = res.json()
    assert users_data.get("success") is True
    assert len(users_data.get("data", [])) > 0
    test_user_id = users_data["data"][0]["id"]
    print(f"[PASS] SabTrack Users & CRM Roster API ({len(users_data['data'])} athletes)")

    # 9. Toggle Pro Status
    res = client.post(f"/api/admin/sabtrack/users/{test_user_id}/toggle-pro")
    assert res.status_code == 200
    print("[PASS] Toggle User Pro Status API")

    # 10. CRM Allot Coach to Athlete
    res = client.post(f"/api/admin/crm/athletes/{test_user_id}/allot-coach", json={
        "coachId": "coach_priya_sharma",
        "coachName": "Coach Priya Sharma",
        "planTier": "elite",
        "notes": "Testing automated allotment"
    })
    assert res.status_code == 200
    print("[PASS] CRM Allot Coach to Athlete API")

    # 11. CRM Update Plan
    res = client.post(f"/api/admin/crm/athletes/{test_user_id}/update-plan", json={
        "tier": "longevity"
    })
    assert res.status_code == 200
    print("[PASS] CRM Update Athlete Plan Tier API")

    # 12. CRM Batch Allot
    res = client.post("/api/admin/crm/athletes/batch-allot", json={
        "athleteIds": [test_user_id],
        "coachId": "coach_marcus_vance",
        "coachName": "Dr. Marcus Vance",
        "planTier": "elite",
        "notes": "Batch assignment test"
    })
    assert res.status_code == 200
    print("[PASS] CRM Batch Allot API")

    # 13. Consultation Requests
    res = client.get("/api/admin/consultations/requests")
    assert res.status_code == 200
    req_data = res.json()
    assert req_data.get("success") is True
    assert len(req_data.get("data", [])) > 0
    test_req_id = req_data["data"][0]["id"]
    print(f"[PASS] Consultations Requests API ({len(req_data['data'])} requests)")

    # 14. Place Coach for Consultation
    res = client.post(f"/api/admin/consultations/{test_req_id}/place-coach", json={
        "coachId": "coach_priya_sharma",
        "coachName": "Coach Priya Sharma"
    })
    assert res.status_code == 200
    print("[PASS] Place Coach for Consultation API")

    # 15. Coach Payout Ledger
    res = client.get("/api/admin/coach-payouts?commission_rate=15.0")
    assert res.status_code == 200
    payouts = res.json()
    assert payouts.get("success") is True
    assert len(payouts.get("data", [])) > 0
    test_pay_id = payouts["data"][0]["id"]
    print(f"[PASS] Coach Payout Ledger API ({len(payouts['data'])} payout items)")

    # 16. Settle Coach Payout
    res = client.post(f"/api/admin/coach-payouts/{test_pay_id}/settle", json={
        "transactionRef": "TXN-TEST-123456"
    })
    assert res.status_code == 200
    print("[PASS] Settle Coach Payout API")

    # 17. Coach Applications Queue
    res = client.get("/api/admin/coach-applications")
    assert res.status_code == 200
    apps_data = res.json()
    assert apps_data.get("success") is True
    assert len(apps_data.get("data", [])) > 0
    print(f"[PASS] Coach Applications Queue API ({len(apps_data['data'])} applications)")

    # 18. Submit Coach Application
    res = client.post("/api/admin/coach-applications", json={
        "name": "Candidate Jane Doe",
        "email": "jane.doe@nutritionhealth.org",
        "phone": "+91 99887 66554",
        "domain": "Clinical Sports Nutrition",
        "experienceYears": "4-6 Years",
        "aboutWork": "Specialized in metabolic rate and macro optimization",
        "clientCount": 20
    })
    assert res.status_code == 200
    new_app_id = res.json()["data"]["id"]
    print("[PASS] Submit Coach Application API")

    # 19. Approve Application
    res = client.post(f"/api/admin/coach-applications/{new_app_id}/approve", json={
        "tempPassword": "TempPassword999!"
    })
    assert res.status_code == 200
    print("[PASS] Approve Coach Application API")

    print("\nALL 19 ADMIN BACKEND API SUITES PASSED FLAWLESSLY!")

if __name__ == "__main__":
    run_tests()
