import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_bidirectional_consistency():
    print("=== Testing Bidirectional Data Consistency Across Ecosystem ===")

    # 1. Provision a unique test coach
    coach_email = "marissa.chen@sabcoach.com"
    coach_name = "Coach Marissa Chen"
    res = client.post("/api/admin/coaches", json={
        "name": coach_name,
        "email": coach_email,
        "password": "Password2026!@",
        "role": "Endurance & VO2 Max Specialist",
        "practiceName": "Marissa Endurance Lab"
    })
    assert res.status_code == 200, f"Provision coach failed: {res.text}"
    coach_id = res.json()["coach"]["id"]
    print(f"[PASS] 1. Coach provisioned with ID: {coach_id}")

    # Verify coach appears in coach roster
    res = client.get("/api/admin/coaches")
    assert res.status_code == 200
    all_coaches = res.json()["data"]
    found_coach = next((c for c in all_coaches if c["id"] == coach_id), None)
    assert found_coach is not None, "Provisioned coach not found in getCoaches!"
    assert found_coach["name"] == coach_name
    print("[PASS] 2. Coach verified in master coaches overview")

    # 2. Pick an athlete and allot to this new coach under Elite tier (₹6,000)
    athlete_id = "usr-2"  # Ananya Deshmukh
    res = client.post(f"/api/admin/crm/athletes/{athlete_id}/allot-coach", json={
        "coachId": coach_id,
        "coachName": coach_name,
        "planTier": "elite",
        "notes": "Endurance pacing and cardio metabolic efficiency protocol"
    })
    assert res.status_code == 200, f"Allotment failed: {res.text}"
    print(f"[PASS] 3. Athlete {athlete_id} successfully allotted to {coach_name}")

    # Verify athlete in CRM has assigned coach
    res = client.get("/api/admin/sabtrack/users")
    assert res.status_code == 200
    all_users = res.json()["data"]
    athlete_record = next((u for u in all_users if u["id"] == athlete_id), None)
    assert athlete_record is not None
    assert athlete_record["assignedCoach"] == coach_name
    assert athlete_record["assignedCoachId"] == coach_id
    assert athlete_record["subscriptionTier"] == "elite"
    assert athlete_record["consultationPlan"] == "elite"
    print(f"[PASS] 4. CRM Athlete Record verified with assigned coach & Elite tier")

    # Verify Coach Deep-Dive now lists this athlete
    res = client.get(f"/api/admin/coaches/{coach_id}/deep-dive")
    assert res.status_code == 200
    deep_dive = res.json()
    deep_dive_clients = deep_dive["clients"]["items"]
    matching_client = next((cl for cl in deep_dive_clients if cl["name"] == athlete_record["name"] or cl.get("user_id") == athlete_id), None)
    assert matching_client is not None, "Allotted athlete not found in coach deep-dive client roster!"
    print(f"[PASS] 5. Coach 360 Deep-Dive verified: athlete appears in coach's active caseload")

    # Verify Payout Ledger dynamically calculates commission & net payout
    res = client.get("/api/admin/coach-payouts?commission_rate=15.0")
    assert res.status_code == 200
    payout_items = res.json()["data"]
    coach_payout = next((p for p in payout_items if p["athleteId"] == athlete_id and p["coachId"] == coach_id), None)
    assert coach_payout is not None, "Payout ledger missing record for newly allotted athlete!"
    assert coach_payout["planAmount"] == 6000, f"Expected 6000, got {coach_payout['planAmount']}"
    assert coach_payout["platformTakeRatePct"] == 15.0
    assert coach_payout["platformTakeAmount"] == 900, f"Expected 900 platform take, got {coach_payout['platformTakeAmount']}"
    assert coach_payout["coachNetPayout"] == 5100, f"Expected 5100 coach net, got {coach_payout['coachNetPayout']}"
    print(f"[PASS] 6. Payout Ledger verified: Gross INR 6000 -> Platform INR 900 (15%) -> Coach Net INR 5100")

    # Settle the payout
    payout_id = coach_payout["id"]
    txn_ref = "TXN-SAB-VERIFIED-998877"
    res = client.post(f"/api/admin/coach-payouts/{payout_id}/settle", json={
        "transactionRef": txn_ref
    })
    assert res.status_code == 200
    print(f"[PASS] 7. Payout {payout_id} marked as settled with ref {txn_ref}")

    # Verify payout ledger persists settled status
    res = client.get("/api/admin/coach-payouts?commission_rate=15.0")
    assert res.status_code == 200
    updated_payout_items = res.json()["data"]
    settled_record = next((p for p in updated_payout_items if p["id"] == payout_id), None)
    assert settled_record is not None
    assert settled_record["status"] == "settled"
    assert settled_record["transactionRef"] == txn_ref
    print("[PASS] 8. Persistent Settlement Ledger verified: status=settled and transaction ref preserved")

    # 3. Test Consultation Placement
    # First create a consultation request
    res = client.post("/api/admin/consultations/requests", json={
        "athleteName": "Suresh Raina",
        "athleteEmail": "suresh.raina@testcricket.in",
        "athletePhone": "+91 99112 33445",
        "planId": "longevity",
        "planName": "03 — LONGEVITY (Biohacking & Wellness)",
        "planPrice": "Premium",
        "primaryGoals": "Cardiovascular resilience and deep sleep recovery"
    })
    assert res.status_code == 200
    new_req_id = res.json()["data"]["id"]
    print(f"[PASS] 9. New consultation inquiry logged ({new_req_id})")

    # Place with Coach Marissa Chen
    res = client.post(f"/api/admin/consultations/{new_req_id}/place-coach", json={
        "coachId": coach_id,
        "coachName": coach_name
    })
    assert res.status_code == 200
    print("[PASS] 10. Consultation inquiry placed with Coach")

    # Verify request status is placed
    res = client.get("/api/admin/consultations/requests")
    assert res.status_code == 200
    req_list = res.json()["data"]
    placed_req = next((r for r in req_list if r["id"] == new_req_id), None)
    assert placed_req is not None
    assert placed_req["status"] == "placed"
    assert placed_req["placedCoachName"] == coach_name
    print("[PASS] 11. Consultation request status verified as 'placed'")

    # Clean up test coach
    res = client.delete(f"/api/admin/coaches/{coach_id}")
    assert res.status_code == 200
    print(f"[PASS] 12. Test Coach {coach_id} cleaned up successfully")

    print("\nALL BIDIRECTIONAL CROSS-FEATURE DATA CONSISTENCY TESTS PASSED! 100% OK")

if __name__ == "__main__":
    test_bidirectional_consistency()
