import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from fastapi.testclient import TestClient
from app.main import app
from app.repositories.coach_repository import coach_repo
from app.repositories.db_repository import db_repository

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("RUNNING E2E CROSS-PLATFORM NOTIFICATIONS & WORKFLOW TESTS")
    print("=" * 60)

    # 1. Coach creates profile
    coach_id = "coach_test_pro"
    profile_payload = {
        "id": coach_id,
        "name": "Coach Samantha Ray",
        "title": "Head Strength & Biomechanics Specialist",
        "specialty": "Olympic Lifting & Functional Hypertrophy",
        "bio": "Certified CSCS with 10+ years coaching elite athletes.",
        "avatar": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=200",
        "rating": 4.97,
        "active_clients": 15
    }
    r = client.post("/api/coach/profile", json=profile_payload, headers={"Authorization": f"Bearer mock-token-{coach_id}"})
    assert r.status_code == 200, f"Profile save failed: {r.text}"
    print("[PASS] Coach profile saved successfully")

    # 2. Coach creates a Program
    program_id = "prog_e2e_101"
    program_payload = {
        "id": program_id,
        "coach_id": coach_id,
        "name": "12-Week Hybrid Athlete Architecture",
        "title": "12-Week Hybrid Athlete Architecture",
        "description": "Periodized undulating hypertrophy split with concurrent aerobic capacity.",
        "durationWeeks": 12,
        "duration_weeks": 12,
        "level": "Advanced",
        "category": "Hypertrophy",
        "assignedClientIds": []
    }
    r = client.post("/api/coach/programs", json=program_payload, headers={"Authorization": f"Bearer mock-token-{coach_id}"})
    assert r.status_code == 200, f"Program create failed: {r.text}"
    print("[PASS] Program created successfully")

    # 3. Coach sends coaching invitation to SabTrack athlete
    athlete_uid = "usr_athlete_e2e"
    req_payload = {
        "coach_id": coach_id,
        "coach_name": "Coach Samantha Ray",
        "sabtrack_user_id": athlete_uid,
        "name": "Rohan Mehra",
        "email": "rohan.mehra@example.com",
        "goal": "Hypertrophy & Conditioning",
        "program_name": "12-Week Hybrid Athlete Architecture"
    }
    r = client.post("/api/coach/clients/send-request", json=req_payload, headers={"Authorization": f"Bearer mock-token-{coach_id}"})
    assert r.status_code == 200, f"Send request failed: {r.text}"
    data = r.json()
    assert data["success"] is True
    client_record_id = data["data"]["id"]
    print(f"[PASS] Coaching invitation dispatched to athlete ({athlete_uid}). Client ID: {client_record_id}")

    # Check athlete received coaching_request in-app notification
    notifs = db_repository.get_notifications(athlete_uid)
    coach_req_notifs = [n for n in notifs if n.get("notif_type") == "coaching_request"]
    assert len(coach_req_notifs) > 0, "Athlete did not receive coaching_request notification"
    print("[PASS] Cross-platform in-app notification verified on athlete device")

    # 4. Athlete checks /coach/my-coach BEFORE accepting -> should show pending_invitation, has_coach: False
    r = client.get("/api/coach/my-coach", headers={"Authorization": f"Bearer mock-token-{athlete_uid}"})
    assert r.status_code == 200
    my_coach_pre = r.json()
    assert my_coach_pre["has_coach"] is False
    assert my_coach_pre["pending_invitation"] is not None
    print("[PASS] Athlete status before acceptance: has_coach is False, pending invitation shown")

    # 5. Athlete ACCEPTS coaching request
    r = client.post(
        f"/api/coach/clients/{client_record_id}/respond-request",
        json={"accept": True, "coach_id": coach_id},
        headers={"Authorization": f"Bearer mock-token-{athlete_uid}"}
    )
    assert r.status_code == 200, f"Accept failed: {r.text}"
    print("[PASS] Athlete accepted coaching request")

    # Check coach received coaching_accepted notification
    coach_notifs = db_repository.get_notifications(coach_id)
    accepted_notifs = [n for n in coach_notifs if n.get("notif_type") == "coaching_accepted"]
    assert len(accepted_notifs) > 0, "Coach did not receive coaching_accepted notification"
    print("[PASS] Coach received cross-platform acceptance notification")

    # 6. Coach ASSIGNS program to athlete
    r = client.post(
        f"/api/coach/programs/{program_id}/assign",
        json={
            "coach_id": coach_id,
            "coach_name": "Coach Samantha Ray",
            "client_ids": [client_record_id],
            "start_date": "Next Monday",
            "frequency": "5 sessions/week"
        },
        headers={"Authorization": f"Bearer mock-token-{coach_id}"}
    )
    assert r.status_code == 200, f"Assign program failed: {r.text}"
    assign_res = r.json()
    assert assign_res["success"] is True
    print("[PASS] Program assigned to athlete on backend")

    # Check athlete received program_assigned notification
    athlete_notifs = db_repository.get_notifications(athlete_uid)
    prog_assigned_notifs = [n for n in athlete_notifs if n.get("notif_type") == "program_assigned"]
    assert len(prog_assigned_notifs) > 0, "Athlete did not receive program_assigned notification"
    print(f"[PASS] Athlete received program_assigned notification: '{prog_assigned_notifs[0]['title']}'")

    # 7. Coach SHARES program
    r = client.post(
        f"/api/coach/programs/{program_id}/share",
        json={
            "coach_id": coach_id,
            "client_ids": [client_record_id]
        },
        headers={"Authorization": f"Bearer mock-token-{coach_id}"}
    )
    assert r.status_code == 200
    share_data = r.json()
    assert share_data["success"] is True
    assert "https://sabtrack.in/programs/" in share_data["share_url"]
    print(f"[PASS] Program shared with link: {share_data['share_url']}")

    # 8. Athlete checks /coach/my-coach AFTER acceptance and assignment
    r = client.get("/api/coach/my-coach", headers={"Authorization": f"Bearer mock-token-{athlete_uid}"})
    assert r.status_code == 200
    my_coach_post = r.json()
    assert my_coach_post["has_coach"] is True
    coach_obj = my_coach_post["coach"]
    assert coach_obj["name"] == "Coach Samantha Ray", f"Expected Coach Samantha Ray, got {coach_obj.get('name')}"
    assert "Aryan Mehta" not in coach_obj["name"], "Mocked coach Aryan Mehta still returned!"
    
    assigned_prog = my_coach_post["assigned_program"]
    assert assigned_prog is not None, "Assigned program is missing from my-coach response"
    assert "12-Week Hybrid Athlete Architecture" in assigned_prog["name"]
    print(f"[PASS] Athlete live state verified: Connected to REAL coach '{coach_obj['name']}' with assigned program '{assigned_prog['name']}'")

    # 9. Brand new athlete with NO coach calls /coach/my-coach
    r = client.get("/api/coach/my-coach", headers={"Authorization": "Bearer mock-token-brand_new_user_xyz"})
    assert r.status_code == 200
    new_user_res = r.json()
    assert new_user_res["has_coach"] is False, "Brand new user should NOT have coach"
    assert new_user_res.get("client") is None, "Brand new user should not have matched client"
    print("[PASS] Brand new user with no coach verified: has_coach is False, no fake coach forced")

    print("\n" + "=" * 60)
    print("ALL CROSS-PLATFORM & ECOSYSTEM E2E TESTS PASSED (100%)!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
