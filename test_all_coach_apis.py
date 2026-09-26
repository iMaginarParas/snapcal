import sys
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_all_api_checks():
    passed = 0
    failed = 0
    total = 0

    def assert_check(name, condition, details=""):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name} -> {details}")

    print("\n=================================================================")
    print("      SABCOACH & SABTRACK COMPREHENSIVE BACKEND API AUDIT        ")
    print("=================================================================\n")

    # 1. Health & Core
    print("--- 1. Health & Service Integrity ---")
    r = client.get("/health")
    assert_check("Health Check returns 200", r.status_code == 200, r.text)
    assert_check("Health status is healthy", r.json().get("status") == "healthy")

    # 2. Clients Suite
    print("\n--- 2. Coach Clients Management Suite ---")
    new_client = {
        "id": "test-c-999",
        "name": "Ananya Sharma",
        "email": "ananya.fit@example.com",
        "phone": "+91 98111 22334",
        "status": "Active",
        "goal": "Recomposition & Biomechanics",
        "target_cals": 1950,
        "coach_id": "coach_default"
    }
    r = client.post("/api/coach/clients", json=new_client)
    assert_check("POST /api/coach/clients (Create/Update)", r.status_code == 200, r.text)

    r = client.get("/api/coach/clients")
    assert_check("GET /api/coach/clients (List with Telemetry)", r.status_code == 200, r.text)
    clients_data = r.json().get("data", [])
    found = any(c.get("id") == "test-c-999" or c.get("name") == "Ananya Sharma" for c in clients_data)
    assert_check("Client verified in roster", found)

    # Telemetry & feedback
    r = client.get("/api/coach/client/test-c-999/telemetry?date=2026-09-26")
    assert_check("GET /api/coach/client/{id}/telemetry", r.status_code == 200, r.text)

    r = client.post("/api/coach/client/test-c-999/feedback", json={
        "client_id": "test-c-999",
        "date": "2026-09-26",
        "feedback_text": "Hit all protein targets flawlessly today!",
        "rating": "great"
    })
    # SabTrack User Directory Search & Invite
    r = client.get("/api/coach/sabtrack-users/search?q=arjun")
    assert_check("GET /api/coach/sabtrack-users/search (SabTrack User Verification)", r.status_code == 200, r.text)
    assert_check("SabTrack User Search returns verified candidates", len(r.json().get("data", [])) > 0)

    r = client.post("/api/coach/clients/invite", json={
        "name": "Tanvi Gupta",
        "email": "tanvi.g@example.com",
        "phone": "+91 99887 76655",
        "goal": "Marathon Performance"
    })
    assert_check("POST /api/coach/clients/invite (Generate SabTrack Pairing Link)", r.status_code == 200, r.text)
    assert_check("Invite response contains invite_code & invite_link", "invite_code" in r.json().get("data", {}))

    # 3. Programs Suite
    print("\n--- 3. Programs Suite & AI Blueprint ---")
    prog_payload = {
        "id": "prog-test-101",
        "title": "12-Week Hypertrophy Architecture",
        "description": "Periodized undulating hypertrophy split with deload weeks",
        "duration_weeks": 12,
        "difficulty": "Advanced",
        "category": "Hypertrophy",
        "coach_id": "coach_default",
        "schedule": [{"week": 1, "focus": "Accumulation Phase"}]
    }
    r = client.post("/api/coach/programs", json=prog_payload)
    assert_check("POST /api/coach/programs", r.status_code == 200, r.text)

    r = client.get("/api/coach/programs")
    assert_check("GET /api/coach/programs", r.status_code == 200, r.text)

    r = client.post("/api/coach/ai/generate-program", json={
        "prompt": "Create a 6-week fat loss and barbell strength program for intermediate athletes",
        "goal": "Fat Loss",
        "experience": "Intermediate"
    })
    assert_check("POST /api/coach/ai/generate-program", r.status_code == 200, r.text)

    # 4. Workouts Suite
    print("\n--- 4. Workouts Suite & AI Workout Builder ---")
    w_payload = {
        "id": "wo-test-101",
        "name": "Upper Body Push Power",
        "category": "Chest & Shoulders",
        "difficulty": "Intermediate",
        "duration": "55 min",
        "coach_id": "coach_default",
        "exercises": [
            {"name": "Incline Dumbbell Press", "sets": 4, "reps": "8-10", "weight": 32}
        ]
    }
    r = client.post("/api/coach/workouts", json=w_payload)
    assert_check("POST /api/coach/workouts", r.status_code == 200, r.text)

    r = client.get("/api/coach/workouts")
    assert_check("GET /api/coach/workouts", r.status_code == 200, r.text)

    r = client.post("/api/coach/ai/generate-workout", json={
        "focus": "Posterior Chain Deadlift Focus",
        "difficulty": "Advanced"
    })
    assert_check("POST /api/coach/ai/generate-workout", r.status_code == 200, r.text)

    # 5. Sessions & Calendar Suite
    print("\n--- 5. Sessions & Scheduling Suite ---")
    sess_payload = {
        "id": "sess-test-101",
        "client_name": "Ananya Sharma",
        "title": "Weekly 1:1 Form & Bio Review",
        "date": "2026-09-28",
        "time": "10:00 AM",
        "duration": "50 min",
        "type": "1:1 Coaching",
        "status": "Scheduled",
        "coach_id": "coach_default"
    }
    r = client.post("/api/coach/sessions", json=sess_payload)
    assert_check("POST /api/coach/sessions", r.status_code == 200, r.text)

    r = client.get("/api/coach/sessions")
    assert_check("GET /api/coach/sessions", r.status_code == 200, r.text)

    # Availability
    avail_payload = [
        {"day": "Monday", "enabled": True, "slots": ["09:00 - 12:00", "15:00 - 18:00"]},
        {"day": "Tuesday", "enabled": True, "slots": ["09:00 - 12:00"]}
    ]
    r = client.put("/api/coach/availability", json=avail_payload)
    assert_check("PUT /api/coach/availability", r.status_code == 200, r.text)

    r = client.get("/api/coach/availability")
    assert_check("GET /api/coach/availability", r.status_code == 200, r.text)

    # 6. Diet Plans & Dispatcher Suite
    print("\n--- 6. Diet Plans & Nutrition Suite ---")
    r = client.get("/api/diet-plans")
    assert_check("GET /api/diet-plans", r.status_code == 200, r.text)

    r = client.post("/api/diet-plans/send-daily", json={
        "client_id": "test-c-999",
        "client_name": "Ananya Sharma",
        "target_date": "2026-09-26",
        "title": "Clean Macro Prescription",
        "total_calories": 1950,
        "protein_g": 140,
        "carbs_g": 190,
        "fats_g": 55,
        "meals": [
            {
                "slot_name": "Breakfast",
                "time": "08:30",
                "target_calories": 500,
                "foods": [{"name": "Greek Yogurt & Berries", "portion": "250g", "calories": 250, "protein": 25}]
            }
        ]
    })
    assert_check("POST /api/diet-plans/send-daily", r.status_code == 200, r.text)

    r = client.get("/api/client/diet-plan/today?client_id=test-c-999&date=2026-09-26")
    assert_check("GET /api/client/diet-plan/today", r.status_code == 200, r.text)

    # 7. Check-ins Suite
    print("\n--- 7. Check-ins & Review Suite ---")
    chk_payload = {
        "id": "chk-test-101",
        "client_id": "test-c-999",
        "client_name": "Ananya Sharma",
        "date": "2026-09-26",
        "status": "Submitted",
        "adherence": 96,
        "coach_id": "coach_default",
        "notes": "Energy levels high, sleep quality at 88.",
        "metrics": {"weight": 61.2, "energy": 9, "adherence": 96}
    }
    r = client.post("/api/coach/checkins", json=chk_payload)
    assert_check("POST /api/coach/checkins", r.status_code == 200, r.text)

    r = client.get("/api/coach/checkins")
    assert_check("GET /api/coach/checkins", r.status_code == 200, r.text)

    # 8. Direct Messages Suite
    print("\n--- 8. Messages & Real-Time Threads ---")
    msg_payload = {
        "id": "msg-test-101",
        "client_id": "test-c-999",
        "client_name": "Ananya Sharma",
        "coach_id": "coach_default",
        "last_message": "Session confirmed for Monday at 10 AM",
        "messages": [
            {"id": "m1", "sender": "coach", "text": "Session confirmed for Monday at 10 AM", "timestamp": "18:20"}
        ]
    }
    r = client.post("/api/coach/messages", json=msg_payload)
    assert_check("POST /api/coach/messages", r.status_code == 200, r.text)

    r = client.get("/api/coach/messages")
    assert_check("GET /api/coach/messages", r.status_code == 200, r.text)

    # 9. Payments & Packages Suite
    print("\n--- 9. Business, Invoices & Products Suite ---")
    pay_payload = {
        "id": "pay-test-101",
        "client_name": "Ananya Sharma",
        "package_name": "3-Month Elite Transformation",
        "amount": 15000,
        "currency": "INR (₹)",
        "status": "Paid",
        "coach_id": "coach_default"
    }
    r = client.post("/api/coach/payments", json=pay_payload)
    assert_check("POST /api/coach/payments", r.status_code == 200, r.text)

    r = client.get("/api/coach/payments")
    assert_check("GET /api/coach/payments", r.status_code == 200, r.text)

    prod_payload = {
        "id": "prod-test-101",
        "title": "Comprehensive Biomechanics Coaching",
        "price": 4999,
        "duration": "1 Month",
        "features": ["Weekly 1:1 Video", "Daily Diet Telemetry", "Workout Programming"],
        "coach_id": "coach_default"
    }
    r = client.post("/api/coach/products", json=prod_payload)
    assert_check("POST /api/coach/products", r.status_code == 200, r.text)

    r = client.get("/api/coach/products")
    assert_check("GET /api/coach/products", r.status_code == 200, r.text)

    # 10. Leads CRM Pipeline
    print("\n--- 10. Leads CRM & Conversion Pipeline ---")
    lead_payload = {
        "id": "lead-test-101",
        "name": "Rohan Mehra",
        "email": "rohan.m@example.com",
        "phone": "+91 99000 11223",
        "stage": "Qualified",
        "goal": "Marathon Preparation & Conditioning",
        "source": "Instagram DM",
        "value": 12000,
        "coach_id": "coach_default"
    }
    r = client.post("/api/coach/leads", json=lead_payload)
    assert_check("POST /api/coach/leads", r.status_code == 200, r.text)

    r = client.get("/api/coach/leads")
    assert_check("GET /api/coach/leads", r.status_code == 200, r.text)

    # 11. Groups & Challenges
    print("\n--- 11. Community Groups & Challenges ---")
    grp_payload = {
        "id": "grp-test-101",
        "name": "Summer Lean Hypertrophy Squad",
        "category": "Strength",
        "coach_id": "coach_default",
        "description": "Squad accountability and daily log sharing"
    }
    r = client.post("/api/coach/groups", json=grp_payload)
    assert_check("POST /api/coach/groups", r.status_code == 200, r.text)

    r = client.get("/api/coach/groups")
    assert_check("GET /api/coach/groups", r.status_code == 200, r.text)

    chal_payload = {
        "id": "chal-test-101",
        "title": "10,000 Steps Daily 30-Day Sprint",
        "category": "Endurance & Steps",
        "prize": "Custom Nutrition Protocol & Merch",
        "coach_id": "coach_default"
    }
    r = client.post("/api/coach/challenges", json=chal_payload)
    assert_check("POST /api/coach/challenges", r.status_code == 200, r.text)

    r = client.get("/api/coach/challenges")
    assert_check("GET /api/coach/challenges", r.status_code == 200, r.text)

    # 12. Automations & Reports
    print("\n--- 12. Automations & Practice Reports ---")
    auto_payload = {
        "id": "auto-test-101",
        "title": "Welcome Email & Onboarding Questionnaire",
        "trigger": "New Client Added",
        "action": "Dispatch Protocol + Send Invite Link",
        "active": True,
        "coach_id": "coach_default"
    }
    r = client.post("/api/coach/automations", json=auto_payload)
    assert_check("POST /api/coach/automations", r.status_code == 200, r.text)

    r = client.get("/api/coach/automations")
    assert_check("GET /api/coach/automations", r.status_code == 200, r.text)

    rep_payload = {
        "id": "rep-test-101",
        "client_name": "Ananya Sharma",
        "period": "September Progress Audit",
        "coach_id": "coach_default",
        "coach_notes": "Adherence maintained above 95% for 4 consecutive weeks."
    }
    r = client.post("/api/coach/reports", json=rep_payload)
    assert_check("POST /api/coach/reports", r.status_code == 200, r.text)

    r = client.get("/api/coach/reports")
    assert_check("GET /api/coach/reports", r.status_code == 200, r.text)

    # Cleanup test client
    client.delete("/api/coach/clients/test-c-999")

    print("\n=================================================================")
    print(f"      AUDIT SUMMARY: {passed} PASSED, {failed} FAILED (TOTAL {total})")
    print("=================================================================\n")

    return failed == 0

if __name__ == "__main__":
    success = run_all_api_checks()
    sys.exit(0 if success else 1)
