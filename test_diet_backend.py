from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_unified_diet_api():
    print("--- 1. Testing GET /api/diet-plans ---")
    res = client.get("/api/diet-plans")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    plans = res.json()["data"]
    print(f"Retrieved {len(plans)} plans/templates. First: {plans[0]['title']}")
    assert len(plans) >= 3

    print("\n--- 2. Testing POST /api/diet-plans/send-daily ---")
    send_payload = {
        "client_id": "c1",
        "client_name": "Marcus Vance",
        "target_date": "2026-09-21",
        "title": "Hypertrophy Cutting Day 1",
        "description": "High protein, timed carbs around 5 PM workout",
        "total_calories": 2250,
        "protein_g": 180.0,
        "carbs_g": 200.0,
        "fats_g": 60.0,
        "water_liters": 3.8,
        "supplements": ["Creatine 5g", "Whey Isolate 30g", "Omega-3 2000mg"],
        "instructions": "Drink 1L water before noon. Take creatine post-workout.",
        "meals": [
            {
                "slot_name": "Breakfast",
                "time": "08:30",
                "target_calories": 550,
                "target_protein": 45.0,
                "target_carbs": 50.0,
                "target_fats": 15.0,
                "foods": [
                    {"name": "Whole Eggs & Egg Whites", "portion": "2 eggs + 100g whites", "calories": 220, "protein": 24.0, "carbs": 1.0, "fats": 11.0},
                    {"name": "Oatmeal with blueberries", "portion": "60g oats", "calories": 240, "protein": 8.0, "carbs": 42.0, "fats": 3.5}
                ]
            }
        ]
    }
    res_send = client.post("/api/diet-plans/send-daily", json=send_payload)
    assert res_send.status_code == 200, res_send.text
    print("Dispatch result:", res_send.json()["message"])

    print("\n--- 3. Testing GET /api/client/diet-plan/today for SabTrack ---")
    res_client = client.get("/api/client/diet-plan/today?client_id=c1&date=2026-09-21")
    assert res_client.status_code == 200, res_client.text
    client_data = res_client.json()
    assert client_data["has_plan"] is True
    print(f"Client c1 received plan: {client_data['plan']['title']} with {client_data['plan']['total_calories']} kcal")

    print("\n--- 4. Testing POST /api/diet-plans/generate-ai ---")
    ai_payload = {
        "client_name": "Elena Rostova",
        "goal": "Fat Loss",
        "dietary_preference": "High Protein",
        "target_calories": 1850,
        "allergies": ["Shellfish"]
    }
    res_ai = client.post("/api/diet-plans/generate-ai", json=ai_payload)
    assert res_ai.status_code == 200, res_ai.text
    ai_plan = res_ai.json()["data"]
    print(f"Generated AI Plan: {ai_plan['title']} with {len(ai_plan['meals'])} meals")

    print("\n--- 5. Testing GET /api/coach/clients ---")
    res_coach_clients = client.get("/api/coach/clients")
    assert res_coach_clients.status_code == 200
    coach_clients = res_coach_clients.json()["data"]
    print(f"Coach clients count: {len(coach_clients)}")

    print("\n--- 6. Testing GET /api/coach/client/c1/telemetry ---")
    res_telem = client.get("/api/coach/client/c1/telemetry?date=2026-09-21")
    assert res_telem.status_code == 200
    telem = res_telem.json()["data"]
    print(f"Client c1 Telemetry Status: {telem['status']}, Prescribed Cals: {telem['prescribed']['calories']}")

    print("\n--- 7. Testing POST /api/coach/client/c1/feedback ---")
    fb_payload = {
        "client_id": "c1",
        "date": "2026-09-21",
        "feedback_text": "Great breakfast macro execution! Keep hydration high this afternoon.",
        "rating": "great"
    }
    res_fb = client.post("/api/coach/client/c1/feedback", json=fb_payload)
    assert res_fb.status_code == 200
    print("Feedback saved:", res_fb.json()["message"])

    print("\nAll unified backend endpoints verified successfully!")

if __name__ == "__main__":
    test_unified_diet_api()
