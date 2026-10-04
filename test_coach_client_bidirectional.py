import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from fastapi.testclient import TestClient
from app.main import app
from app.repositories.coach_repository import coach_repo
from app.repositories.db_repository import db_repository

client = TestClient(app)

def run_bidirectional_tests():
    print("=" * 70)
    print("RUNNING BIDIRECTIONAL COACH <-> CLIENT CONSISTENCY TESTS")
    print("=" * 70)

    # ---------------------------------------------------------
    # TEST 1: Coach adds client from website -> Client sees & accepts on mobile app
    # ---------------------------------------------------------
    coach_1 = "coach_test_sam"
    client_uid_1 = "usr_athlete_bi_01"
    client_email_1 = "athlete_bi_01@example.com"

    # Coach sets up profile
    client.post("/api/coach/profile", json={
        "id": coach_1,
        "name": "Coach Samantha",
        "title": "Biomechanics Specialist",
        "specialty": "Fitness & Strength",
        "active_clients": 5
    }, headers={"Authorization": f"Bearer mock-token-{coach_1}"})

    # Coach sends request to athlete
    res = client.post("/api/coach/clients/send-request", json={
        "coach_id": coach_1,
        "coach_name": "Coach Samantha",
        "sabtrack_user_id": client_uid_1,
        "name": "Athlete One",
        "email": client_email_1,
        "goal": "Strength Gain"
    }, headers={"Authorization": f"Bearer mock-token-{coach_1}"})
    assert res.status_code == 200
    c_rec_id = res.json()["data"]["id"]
    print("[PASS] Coach sent request to client. Client ID:", c_rec_id)

    # Coach checks website client list -> Client is listed as Pending Client Approval
    res = client.get("/api/coach/clients", headers={"Authorization": f"Bearer mock-token-{coach_1}"})
    assert res.status_code == 200
    coach_clients = res.json().get("data", [])
    matched_on_coach_site = next((c for c in coach_clients if c["id"] == c_rec_id), None)
    assert matched_on_coach_site is not None
    assert "Pending" in matched_on_coach_site["status"]
    print("[PASS] Coach website client list displays client with Pending status")

    # Client checks mobile app (/my-coach) -> pending_invitation is present
    res = client.get("/api/coach/my-coach", headers={"Authorization": f"Bearer mock-token-{client_uid_1}"})
    assert res.status_code == 200
    my_coach_data = res.json()
    assert my_coach_data["has_coach"] is False
    assert my_coach_data["pending_invitation"] is not None
    assert my_coach_data["pending_invitation"]["id"] == c_rec_id
    print("[PASS] Mobile app shows pending invitation card to client")

    # Client accepts request from mobile app
    res = client.post(f"/api/coach/clients/{c_rec_id}/respond-request", json={
        "accept": True,
        "coach_id": coach_1
    }, headers={"Authorization": f"Bearer mock-token-{client_uid_1}"})
    assert res.status_code == 200
    print("[PASS] Client accepted invitation from mobile app")

    # Client checks mobile app -> Now has_coach is True, coach details match Coach Samantha
    res = client.get("/api/coach/my-coach", headers={"Authorization": f"Bearer mock-token-{client_uid_1}"})
    assert res.status_code == 200
    my_coach_active = res.json()
    assert my_coach_active["has_coach"] is True
    assert my_coach_active["coach"]["name"] == "Coach Samantha"
    print("[PASS] Mobile app now confirms active connection to Coach Samantha")

    # Coach checks website client list -> Status is now Active, sabtrack connected is True
    res = client.get("/api/coach/clients", headers={"Authorization": f"Bearer mock-token-{coach_1}"})
    assert res.status_code == 200
    coach_clients_post = res.json().get("data", [])
    active_client = next((c for c in coach_clients_post if c["id"] == c_rec_id), None)
    assert active_client is not None
    assert active_client["status"] == "Active"
    assert active_client.get("sabtrack_data", {}).get("connected") is True
    print("[PASS] Coach website client list confirms client is Active and connected")

    # ---------------------------------------------------------
    # TEST 2: Client connects to coach directly from mobile app -> Coach sees on website
    # ---------------------------------------------------------
    coach_2 = "coach_marcus_vance"
    client_uid_2 = "usr_athlete_bi_02"
    client_email_2 = "athlete_bi_02@example.com"

    res = client.post("/api/coach/connect-coach", json={
        "coach_id": coach_2,
        "name": "Athlete Two",
        "email": client_email_2,
        "user_id": client_uid_2,
        "goal": "Metabolic Health"
    }, headers={"Authorization": f"Bearer mock-token-{client_uid_2}"})
    assert res.status_code == 200
    client_2_record = res.json()["client"]
    client_2_id = client_2_record["id"]
    print("[PASS] Client connected directly to Dr. Marcus Vance. Record ID:", client_2_id)

    # Client checks mobile app -> has_coach is True, coach is Marcus Vance
    res = client.get("/api/coach/my-coach", headers={"Authorization": f"Bearer mock-token-{client_uid_2}"})
    assert res.status_code == 200
    client_2_app = res.json()
    assert client_2_app["has_coach"] is True
    assert "Marcus Vance" in client_2_app["coach"]["name"]
    print("[PASS] Mobile app shows athlete 2 connected to Dr. Marcus Vance")

    # Coach checks website client list -> Athlete Two is in coach's client list as Active
    res = client.get("/api/coach/clients", headers={"Authorization": f"Bearer mock-token-{coach_2}"})
    assert res.status_code == 200
    coach_2_clients = res.json().get("data", [])
    found_athlete_2 = next((c for c in coach_2_clients if c["email"] == client_email_2 or c["id"] == client_2_id), None)
    assert found_athlete_2 is not None
    assert found_athlete_2["status"] == "Active"
    assert found_athlete_2.get("sabtrack_data", {}).get("connected") is True
    print("[PASS] Coach website client list shows Athlete Two as Active and linked")

    # ---------------------------------------------------------
    # TEST 3: Deduplication check - connecting again doesn't duplicate record
    # ---------------------------------------------------------
    res = client.post("/api/coach/connect-coach", json={
        "coach_id": coach_2,
        "name": "Athlete Two",
        "email": client_email_2,
        "user_id": client_uid_2,
        "goal": "Metabolic Health"
    }, headers={"Authorization": f"Bearer mock-token-{client_uid_2}"})
    assert res.status_code == 200
    res_dup = client.get("/api/coach/clients", headers={"Authorization": f"Bearer mock-token-{coach_2}"})
    coach_2_clients_after = res_dup.json().get("data", [])
    count_matches = len([c for c in coach_2_clients_after if c["email"] == client_email_2])
    assert count_matches == 1, f"Expected 1 record for athlete 2, but found {count_matches}"
    print("[PASS] Re-connecting did not create duplicate record in coach_clients")

    # ---------------------------------------------------------
    # TEST 4: Coach invites client via invite code -> Client connects with invite code
    # ---------------------------------------------------------
    coach_3 = "coach_priya_sharma"
    client_uid_3 = "usr_athlete_bi_03"
    client_email_3 = "athlete_bi_03@example.com"

    res = client.post("/api/coach/clients/invite", json={
        "coach_id": coach_3,
        "name": "Athlete Three",
        "email": client_email_3,
        "goal": "Mobility & Yoga"
    }, headers={"Authorization": f"Bearer mock-token-{coach_3}"})
    assert res.status_code == 200
    invite_code = res.json()["data"]["invite_code"]
    print(f"[PASS] Coach invited athlete 3 with code: {invite_code}")

    # Re-sending invite does not create a duplicate
    res_reinvite = client.post("/api/coach/clients/invite", json={
        "coach_id": coach_3,
        "name": "Athlete Three",
        "email": client_email_3,
        "goal": "Mobility & Yoga"
    }, headers={"Authorization": f"Bearer mock-token-{coach_3}"})
    assert res_reinvite.status_code == 200
    res_coach3_clients = client.get("/api/coach/clients", headers={"Authorization": f"Bearer mock-token-{coach_3}"})
    matches_c3 = [c for c in res_coach3_clients.json().get("data", []) if c["email"] == client_email_3]
    assert len(matches_c3) == 1, f"Expected 1 record for athlete 3, found {len(matches_c3)}"
    print("[PASS] Re-inviting with same email deduplicated properly")

    # Athlete connects using invite code from mobile app
    res = client.post("/api/coach/connect-coach", json={
        "invite_code": invite_code,
        "name": "Athlete Three",
        "email": client_email_3,
        "user_id": client_uid_3
    }, headers={"Authorization": f"Bearer mock-token-{client_uid_3}"})
    assert res.status_code == 200
    print("[PASS] Athlete connected using invite code")

    # Athlete checks mobile app
    res = client.get("/api/coach/my-coach", headers={"Authorization": f"Bearer mock-token-{client_uid_3}"})
    assert res.status_code == 200
    my_coach_3 = res.json()
    assert my_coach_3["has_coach"] is True
    assert "Priya Sharma" in my_coach_3["coach"]["name"]
    print("[PASS] Mobile app shows athlete 3 connected to Coach Priya Sharma")

    # Coach checks website
    res = client.get("/api/coach/clients", headers={"Authorization": f"Bearer mock-token-{coach_3}"})
    c3_clients = res.json().get("data", [])
    ath3_in_coach = next((c for c in c3_clients if c["email"] == client_email_3), None)
    assert ath3_in_coach is not None
    assert ath3_in_coach["status"] == "Active"
    assert ath3_in_coach.get("sabtrack_data", {}).get("connected") is True
    print("[PASS] Coach website shows athlete 3 as Active")

    print("\n" + "=" * 70)
    print("ALL BIDIRECTIONAL CONSISTENCY TESTS PASSED! (100%)")
    print("=" * 70)

if __name__ == "__main__":
    run_bidirectional_tests()
