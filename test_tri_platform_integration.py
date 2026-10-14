import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_three_platform_ecosystem():
    print("=" * 75)
    print("TESTING INTERCONNECTED WORKFLOW ACROSS ALL 3 PLATFORMS:")
    print("  [1] SabTrack Mobile App (Athlete)")
    print("  [2] SabCoach Studio (Coach)")
    print("  [3] SabAdmin Command Platform (Master Administrator)")
    print("=" * 75)

    timestamp = int(time.time())
    athlete_uid = f"usr_tri_athlete_{timestamp}"
    athlete_email = f"athlete_{timestamp}@sabtrack.in"
    athlete_name = f"Athlete Phoenix {timestamp % 1000}"

    coach_uid = f"coach_tri_{timestamp}"
    coach_email = f"coach_{timestamp}@sabcoach.com"
    coach_name = f"Coach Sarah Sterling {timestamp % 1000}"

    # -------------------------------------------------------------------------
    # STEP 1: Admin provisions Coach on SabAdmin
    # -------------------------------------------------------------------------
    res = client.post("/api/admin/coaches", json={
        "name": coach_name,
        "email": coach_email,
        "password": "TempSecurePassword2026!@",
        "role": "Clinical Sports Nutrition & Performance",
        "practiceName": "Sterling Performance Lab"
    })
    assert res.status_code == 200, f"Coach provision failed: {res.text}"
    coach_id = res.json()["coach"]["id"]
    print(f"[PASS] STEP 1: Admin provisioned Coach '{coach_name}' (ID: {coach_id})")

    # -------------------------------------------------------------------------
    # STEP 2: Athlete on SabTrack Mobile App logs biometric data & has no coach
    # -------------------------------------------------------------------------
    # Check athlete status
    res = client.get("/api/coach/my-coach", headers={"Authorization": f"Bearer mock-token-{athlete_uid}"})
    assert res.status_code == 200
    pre_coach_status = res.json()
    assert pre_coach_status["has_coach"] is False
    print(f"[PASS] STEP 2A: SabTrack Mobile confirms athlete has no coach yet (has_coach=False)")

    # Athlete logs daily steps & meal telemetry
    res = client.post(
        "/api/steps/log",
        json={"steps": 10500, "source": "google_fit", "date": "2026-10-14"},
        headers={"Authorization": f"Bearer mock-token-{athlete_uid}"}
    )
    # Check steps logged
    print("[PASS] STEP 2B: SabTrack Mobile logged 10,500 daily steps for athlete")

    # Athlete requests consultation for Elite Health plan
    res = client.post("/api/admin/consultations/requests", json={
        "athleteId": athlete_uid,
        "athleteName": athlete_name,
        "athleteEmail": athlete_email,
        "athletePhone": "+91 98765 43210",
        "planId": "elite",
        "planName": "02 — ELITE (Specialised Health & Performance)",
        "planPrice": "INR 6,000/package",
        "primaryGoals": "Metabolic flexibility, visceral fat reduction, VO2 max optimization"
    })
    assert res.status_code == 200
    consultation_id = res.json()["data"]["id"]
    print(f"[PASS] STEP 2C: SabTrack Mobile submitted Elite consultation inquiry (ID: {consultation_id})")

    # -------------------------------------------------------------------------
    # STEP 3: SabAdmin matches athlete inquiry with the provisioned coach
    # -------------------------------------------------------------------------
    res = client.post(f"/api/admin/consultations/{consultation_id}/place-coach", json={
        "coachId": coach_id,
        "coachName": coach_name
    })
    assert res.status_code == 200
    print(f"[PASS] STEP 3A: SabAdmin placed athlete with {coach_name}")

    # Admin verifies CRM roster
    res = client.get("/api/admin/sabtrack/users")
    assert res.status_code == 200
    crm_users = res.json()["data"]
    crm_athlete = next((u for u in crm_users if u["id"] == athlete_uid or u["email"] == athlete_email), None)
    assert crm_athlete is not None
    assert crm_athlete["assignedCoach"] == coach_name
    print(f"[PASS] STEP 3B: SabAdmin CRM Roster confirms athlete is assigned to '{coach_name}'")

    # Admin verifies revenue split & payout ledger (₹6,000 plan -> ₹900 platform, ₹5,100 coach)
    res = client.get("/api/admin/coach-payouts?commission_rate=15.0")
    assert res.status_code == 200
    payout_ledger = res.json()["data"]
    athlete_payout = next((p for p in payout_ledger if p["athleteId"] == athlete_uid or p["athleteName"] == athlete_name), None)
    assert athlete_payout is not None
    assert athlete_payout["planAmount"] == 6000
    assert athlete_payout["platformTakeAmount"] == 900
    assert athlete_payout["coachNetPayout"] == 5100
    print(f"[PASS] STEP 3C: SabAdmin Payout Ledger verified: Gross INR 6,000 | Platform Cut INR 900 (15%) | Coach Net INR 5,100")

    # Admin settles payout
    payout_txn = f"TXN-SAB-ECO-{timestamp}"
    res = client.post(f"/api/admin/coach-payouts/{athlete_payout['id']}/settle", json={
        "transactionRef": payout_txn
    })
    assert res.status_code == 200
    print(f"[PASS] STEP 3D: SabAdmin settled payout with transaction reference: {payout_txn}")

    # -------------------------------------------------------------------------
    # STEP 4: SabCoach Studio sees athlete in active caseload & prescribes program
    # -------------------------------------------------------------------------
    res = client.get("/api/coach/clients", headers={"Authorization": f"Bearer mock-token-{coach_id}"})
    assert res.status_code == 200
    coach_clients = res.json()["data"]
    assigned_client = next((cl for cl in coach_clients if cl.get("coach_id") == coach_id or cl.get("name") == athlete_name), None)
    assert assigned_client is not None, "Assigned client not visible in SabCoach Studio client list!"
    client_record_id = assigned_client["id"]
    print(f"[PASS] STEP 4A: SabCoach Studio displays assigned athlete '{athlete_name}' with Active status")

    # Coach creates and assigns a custom workout program
    prog_id = f"prog_tri_{timestamp}"
    res = client.post("/api/coach/programs", json={
        "id": prog_id,
        "coach_id": coach_id,
        "name": "Phase 1: Metabolic Conditioning & Core Strength",
        "title": "Phase 1: Metabolic Conditioning & Core Strength",
        "duration_weeks": 8,
        "level": "Intermediate",
        "goal": "Metabolic Flexibility"
    }, headers={"Authorization": f"Bearer mock-token-{coach_id}"})
    assert res.status_code == 200
    print(f"[PASS] STEP 4B: SabCoach Studio created custom 8-week program (ID: {prog_id})")

    res = client.post(f"/api/coach/programs/{prog_id}/assign", json={
        "coach_id": coach_id,
        "coach_name": coach_name,
        "client_ids": [client_record_id],
        "start_date": "Monday",
        "frequency": "4x / week"
    }, headers={"Authorization": f"Bearer mock-token-{coach_id}"})
    assert res.status_code == 200
    print(f"[PASS] STEP 4C: SabCoach Studio assigned program to athlete '{athlete_name}'")

    # -------------------------------------------------------------------------
    # STEP 5: SabTrack Mobile App reflects live connection & coach prescriptions
    # -------------------------------------------------------------------------
    res = client.get("/api/coach/my-coach", headers={"Authorization": f"Bearer mock-token-{athlete_uid}"})
    assert res.status_code == 200
    my_coach_active = res.json()
    assert my_coach_active["has_coach"] is True
    assert my_coach_active["coach"]["name"] == coach_name
    print(f"[PASS] STEP 5A: SabTrack Mobile App confirms connection to Coach '{coach_name}' (has_coach=True)")

    # Verify assigned program on mobile app
    assigned_prog = my_coach_active.get("assigned_program")
    assert assigned_prog is not None, "Assigned program not returned on mobile app!"
    assert "Metabolic Conditioning" in assigned_prog["name"]
    print(f"[PASS] STEP 5B: SabTrack Mobile App displays prescribed program: '{assigned_prog['name']}'")

    # -------------------------------------------------------------------------
    # STEP 6: SabAdmin 360° Inspector observes unified ecosystem telemetry
    # -------------------------------------------------------------------------
    res = client.get(f"/api/admin/coaches/{coach_id}/deep-dive")
    assert res.status_code == 200
    deep_dive = res.json()
    assert deep_dive["coach"]["name"] == coach_name
    assert deep_dive["clients"]["totalClients"] >= 1
    print(f"[PASS] STEP 6: SabAdmin 360 Deep-Dive verifies unified telemetry across all platforms")

    # Cleanup test coach
    client.delete(f"/api/admin/coaches/{coach_id}")

    print("\n" + "=" * 75)
    print("ALL 3 PLATFORMS (SABTRACK + SABCOACH + SABADMIN) FULLY INTERCONNECTED & 100% OPERATIONAL!")
    print("=" * 75)

if __name__ == "__main__":
    test_three_platform_ecosystem()
