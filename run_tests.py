import sys
import json
import io
from fastapi.testclient import TestClient
from app.main import app

# Create TestClient
try:
    client = TestClient(app)
except ImportError:
    print("TestClient requires httpx. Please install it.")
    sys.exit(1)

def run_tests():
    passed = 0
    failed = 0

    def assert_status(res, expected, name):
        nonlocal passed, failed
        if res.status_code == expected:
            print(f"[PASS] {name} passed.")
            passed += 1
            return True
        else:
            print(f"[FAIL] {name} failed. Expected {expected}, got {res.status_code}")
            print(f"Response: {res.text}")
            failed += 1
            return False

    print("--- Starting SABTRACK AI Backend Tests ---")
    
    # 1. Health check
    res = client.get("/health")
    assert_status(res, 200, "Health Check")

    # 2. Mock Signup
    res = client.post("/api/auth/signup", json={"email": "test_food@test.com", "password": "password123"})
    assert_status(res, 200, "User Signup")

    # 3. Mock Login
    res = client.post("/api/auth/login", json={"email": "test_food@test.com", "password": "password123"})
    is_login_ok = assert_status(res, 200, "User Login")
    
    token = ""
    if is_login_ok:
        token = res.json().get("token")
        
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Meal Image Analysis
    # Create simple 1x1 pixel JPEG file bytes for test upload
    dummy_jpeg = b'\xff\xd8\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\x27" "#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x37\x00\xff\xd9'
    files = {"image": ("test.jpg", io.BytesIO(dummy_jpeg), "image/jpeg")}
    res = client.post("/api/meal/analyze", files=files, headers=headers)
    is_analyze_ok = assert_status(res, 200, "POST /meal/analyze")
    
    # 5. Save reviewed meal
    if is_analyze_ok:
        analysis_data = res.json().get("data") or {}
        foods_to_save = []
        for food in analysis_data.get("foods", []):
            foods_to_save.append({
                "food_name": food["food_name"],
                "weight_g": food["weight_g"],
                "calories": food["calories"],
                "protein": food["protein"],
                "carbs": food["carbs"],
                "fat": food["fat"],
                "fiber": food["fiber"],
                "confidence": food["confidence"],
                "cooking_method": food["cooking_method"],
                "ingredients": food["ingredients"]
            })
            
        save_payload = {
            "name": analysis_data.get("name") or "Test Chicken Biryani Plate",
            "meal_type": "Lunch",
            "total_calories": analysis_data.get("total_calories") or 350,
            "protein": analysis_data.get("protein") or 15.0,
            "carbs": analysis_data.get("carbs") or 40.0,
            "fat": analysis_data.get("fat") or 12.0,
            "fiber": analysis_data.get("fiber") or 2.0,
            "foods": foods_to_save,
            "date": "2026-06-26"
        }
        res = client.post("/api/meal/save", json=save_payload, headers=headers)
        assert_status(res, 200, "POST /meal/save")
        
        # Test legacy route too
        res = client.post("/api/meal", json=save_payload, headers=headers)
        assert_status(res, 200, "POST /meal (Legacy Alias)")

    # 6. Get Meal History
    res = client.get("/api/meal/history", headers=headers)
    assert_status(res, 200, "GET /meal/history")

    # 7. Get Daily Nutrition
    res = client.get("/api/nutrition/daily?date=2026-06-26", headers=headers)
    assert_status(res, 200, "GET /nutrition/daily")

    # 8. Get Weekly Nutrition
    res = client.get("/api/nutrition/weekly", headers=headers)
    assert_status(res, 200, "GET /nutrition/weekly")

    # 9. Get Foods Search
    res = client.get("/api/foods/search?q=idli", headers=headers)
    assert_status(res, 200, "GET /foods/search")

    # 10. Get Recent Foods
    res = client.get("/api/foods/recent", headers=headers)
    assert_status(res, 200, "GET /foods/recent")

    # 11. Add Favorite Food
    fav_payload = {
        "food_name": "Chicken Biryani",
        "calories": 163,
        "protein": 8.5,
        "carbs": 19.2,
        "fat": 5.8,
        "fiber": 1.2
    }
    res = client.post("/api/foods/favorites", json=fav_payload, headers=headers)
    assert_status(res, 200, "POST /foods/favorites")

    # 12. Get Favorite Foods
    res = client.get("/api/foods/favorites", headers=headers)
    assert_status(res, 200, "GET /foods/favorites")

    # 13. Delete Favorite Food
    res = client.delete("/api/foods/favorites/Chicken Biryani", headers=headers)
    assert_status(res, 200, "DELETE /foods/favorites/{food_name}")

    # 14. Scan Barcode
    res = client.post("/api/foods/barcode", json={"barcode": "12345678"}, headers=headers)
    assert_status(res, 200, "POST /foods/barcode")

    # 15. Save Meal Template
    template_payload = {
        "template_name": "My Standard Breakfast",
        "foods": [
            {
                "food_name": "Idli",
                "weight_g": 100,
                "calories": 98,
                "protein": 2.2,
                "carbs": 21.8,
                "fat": 0.3,
                "fiber": 0.9,
                "confidence": 100.0
            }
        ]
    }
    res = client.post("/api/meal/template", json=template_payload, headers=headers)
    assert_status(res, 200, "POST /meal/template")

    # 16. Get Meal Templates
    res = client.get("/api/meal/templates", headers=headers)
    assert_status(res, 200, "GET /meal/templates")

    # 17. Steps API: Sync
    steps_payload = {
        "date": "2026-06-26",
        "sensor_steps": 4000,
        "health_connect_steps": 3000,
        "final_steps": 4500,
        "distance": 3.2,
        "calories": 180,
        "active_minutes": 45,
        "baseline": 1000,
        "last_sensor_value": 5000
    }
    res = client.post("/api/steps/sync", json=steps_payload, headers=headers)
    assert_status(res, 200, "POST /steps/sync")

    # 18. Steps API: Get Daily
    res = client.get("/api/steps/daily?date=2026-06-26", headers=headers)
    is_get_daily_ok = assert_status(res, 200, "GET /steps/daily")
    if is_get_daily_ok:
        data = res.json().get("data") or {}
        if data.get("final_steps") == 4500:
            print("[PASS] Steps API values match.")
            passed += 1
        else:
            print(f"[FAIL] Steps API value mismatch. Expected 4500, got {data.get('final_steps')}")
            failed += 1

    # 19. Steps API: Get History
    res = client.get("/api/steps/history?days=7", headers=headers)
    assert_status(res, 200, "GET /steps/history")

    # 20. User Profile API: Update Profile and check calculations
    profile_payload = {
        "name": "Test User",
        "username": "testuser",
        "age": 28,
        "gender": "Male",
        "height": 180.0,
        "weight": 85.0,
        "activity_level": "Very Active",
        "target_weight": 80.0,
        "goals": "Lose Weight"
    }
    res = client.put("/api/user/profile", json=profile_payload, headers=headers)
    is_profile_ok = assert_status(res, 200, "PUT /user/profile")
    if is_profile_ok:
        data = res.json().get("data") or {}
        if "bmi" in data and "target_calories" in data:
            print("[PASS] User Profile API calculation validation passed.")
            passed += 1
        else:
            print(f"[FAIL] User Profile API calculation validation failed: {data}")
            failed += 1

    # 21. User Profile API: Get History
    res = client.get("/api/user/profile/history", headers=headers)
    is_history_ok = assert_status(res, 200, "GET /user/profile/history")
    if is_history_ok:
        data = res.json().get("data") or {}
        if "history" in data and len(data["history"]) > 0:
            print("[PASS] User Profile History retrieved successfully.")
            passed += 1
        else:
            print(f"[FAIL] User Profile History retrieval failed: {data}")
            failed += 1

    print("\n--- Test Results Summary ---")
    print(f"Total: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    run_tests()

