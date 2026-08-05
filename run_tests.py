import os
os.environ["PORT"] = "3000"
os.environ["GEMINI_API_KEY"] = "mock_gemini_key_for_testing_purposes"
os.environ["SUPABASE_URL"] = "https://mockprojecturlfortests.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "mockanonpublickeyfortestingpurposesonly"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "mockservicerolekeyfortestingpurposesonly"

from unittest.mock import patch, MagicMock
# Mock the create_client call before importing app modules
create_client_patcher = patch('supabase.create_client', return_value=MagicMock())
create_client_patcher.start()

import sys
import json
import io
import uuid


# ----------------- Mock Database Layer -----------------
STORAGE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "data/storage.json"))

def load_local_db() -> dict:
    if not os.path.exists(STORAGE_FILE):
        os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)
        with open(STORAGE_FILE, "w") as f:
            json.dump({}, f)
    try:
        with open(STORAGE_FILE, "r") as f:
            data = json.load(f)
            for section in ["users", "profiles", "meals", "foodItems", "workouts", "dailyStats", 
                            "measurementLogs", "fastingLogs", "friendships", "challenges", 
                            "userChallenges", "supplements", "referrals", "groups", "groupMembers", 
                            "groupMessages", "exports", "exportAuditLogs", "directMessages",
                            "challengeInvites", "groupInvites", "userBadges", "supplementLogs"]:
                if section not in data:
                    if section in ["challenges", "groups", "directMessages", "challengeInvites",
                                   "groupInvites", "userBadges", "supplementLogs"]:
                        data[section] = []
                    else:
                        data[section] = {}
            return data
    except Exception:
        return {}

def save_local_db(data: dict):
    try:
        os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)
        with open(STORAGE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

class MockUser:
    def __init__(self, user_id: str, email: str):
        self.id = user_id
        self.email = email

class MockSession:
    def __init__(self, token: str):
        self.access_token = token
        self.refresh_token = f"mock-refresh-token-{token}"

class MockAuthResponse:
    def __init__(self, user_id: str, email: str, token: str):
        self.user = MockUser(user_id, email)
        self.session = MockSession(token)

class MockAuth:
    def sign_up(self, credentials: dict) -> MockAuthResponse:
        email = credentials.get("email")
        password = credentials.get("password")
        if not email or not password:
            raise Exception("Email and password required")
        
        db = load_local_db()
        for u in db["users"].values():
            if u.get("email") == email:
                raise Exception("User already exists")
        
        user_id = str(uuid.uuid4())
        user_record = {
            "id": user_id,
            "email": email,
            "username": email.split("@")[0] + "_" + str(uuid.uuid4())[:4],
            "created_at": "2026-07-19T00:00:00Z"
        }
        db["users"][user_id] = user_record
        save_local_db(db)
        
        token = f"mock-token-{user_id}"
        return MockAuthResponse(user_id, email, token)

    def sign_in_with_password(self, credentials: dict) -> MockAuthResponse:
        email = credentials.get("email")
        password = credentials.get("password")
        db = load_local_db()
        for u in db["users"].values():
            if u.get("email") == email:
                user_id = u["id"]
                token = f"mock-token-{user_id}"
                return MockAuthResponse(user_id, email, token)
        raise Exception("Invalid email or password")

    def sign_in_with_id_token(self, credentials: dict) -> MockAuthResponse:
        user_id = "mock-google-user-id"
        db = load_local_db()
        if user_id not in db["users"]:
            db["users"][user_id] = {
                "id": user_id,
                "email": "google_user@test.com",
                "username": "google_user",
                "created_at": "2026-07-19T00:00:00Z"
            }
            save_local_db(db)
        return MockAuthResponse(user_id, "google_user@test.com", f"mock-token-{user_id}")

    def get_user(self, token: str) -> MockAuthResponse:
        if not token or not token.startswith("mock-token-"):
            raise Exception("Invalid session token")
        user_id = token.replace("mock-token-", "")
        db = load_local_db()
        if user_id in db["users"]:
            return MockAuthResponse(user_id, db["users"][user_id]["email"], token)
        raise Exception("User not found")

class MockResponse:
    def __init__(self, data: any):
        self.data = data

class MockQueryBuilder:
    def __init__(self, table: str):
        self.table = table
        self.filters = []
        self.order_by = []
        self.offset_val = 0
        self.limit_val = None
        self.is_single = False
        self.is_maybe_single = False
        self.operation = "select"
        self.payload = None

    def _map_table(self) -> str:
        mapping = {
            "users": "users",
            "profiles": "profiles",
            "workouts": "workouts",
            "daily_stats": "dailyStats",
            "measurement_logs": "measurementLogs",
            "meals": "meals",
            "food_items": "foodItems",
            "fasting_logs": "fastingLogs",
            "supplements": "supplements",
            "friendships": "friendships",
            "challenges": "challenges",
            "user_challenges": "userChallenges",
            "groups": "groups",
            "group_members": "groupMembers",
            "group_messages": "groupMessages",
            "referrals": "referrals",
            "exports": "exports",
            "export_audit_logs": "exportAuditLogs",
            "direct_messages": "directMessages",
            "challenge_invites": "challengeInvites",
            "group_invites": "groupInvites",
            "user_badges": "userBadges",
            "supplement_logs": "supplementLogs",
        }
        return mapping.get(self.table, self.table)


    def select(self, fields: str = "*") -> "MockQueryBuilder":
        self.operation = "select"
        self.select_fields = fields
        return self

    def insert(self, data: any) -> "MockQueryBuilder":
        self.operation = "insert"
        self.payload = data
        return self

    def update(self, data: any) -> "MockQueryBuilder":
        self.operation = "update"
        self.payload = data
        return self

    def upsert(self, data: any, on_conflict: str = None) -> "MockQueryBuilder":
        self.operation = "upsert"
        self.payload = data
        return self

    def delete(self) -> "MockQueryBuilder":
        self.operation = "delete"
        return self

    def eq(self, col: str, val: any) -> "MockQueryBuilder":
        self.filters.append(lambda r: str(r.get(col)) == str(val))
        return self

    def neq(self, col: str, val: any) -> "MockQueryBuilder":
        self.filters.append(lambda r: str(r.get(col)) != str(val))
        return self

    def gte(self, col: str, val: any) -> "MockQueryBuilder":
        self.filters.append(lambda r: r.get(col) is not None and str(r.get(col)) >= str(val))
        return self

    def lte(self, col: str, val: any) -> "MockQueryBuilder":
        self.filters.append(lambda r: r.get(col) is not None and str(r.get(col)) <= str(val))
        return self

    def ilike(self, col: str, val: str) -> "MockQueryBuilder":
        pattern = val.replace("%", "").lower()
        self.filters.append(lambda r: r.get(col) is not None and pattern in str(r.get(col)).lower())
        return self

    def or_(self, filter_str: str, *args, **kwargs) -> "MockQueryBuilder":
        parts = filter_str.split(",")
        conditions = []
        for part in parts:
            if ".eq." in part:
                col, val = part.split(".eq.")
                conditions.append((col, val))
            elif ".ilike." in part:
                col, val = part.split(".ilike.")
                pattern = val.replace("%", "").lower()
                conditions.append((col, pattern, "ilike"))
        
        if conditions:
            def or_filter(r):
                for cond in conditions:
                    if len(cond) == 3 and cond[2] == "ilike":
                        col, pattern = cond[0], cond[1]
                        if r.get(col) is not None and pattern in str(r.get(col)).lower():
                            return True
                    else:
                        col, val = cond[0], cond[1]
                        if str(r.get(col)) == str(val):
                            return True
                return False
            self.filters.append(or_filter)
        return self


    def order(self, col: str, desc: bool = False) -> "MockQueryBuilder":
        self.order_by.append((col, desc))
        return self

    def limit(self, val: int) -> "MockQueryBuilder":
        self.limit_val = val
        return self

    def range(self, start: int, end: int) -> "MockQueryBuilder":
        self.offset_val = start
        self.limit_val = end - start + 1
        return self

    def single(self) -> "MockQueryBuilder":
        self.is_single = True
        return self

    def maybe_single(self) -> "MockQueryBuilder":
        self.is_maybe_single = True
        return self

    def execute(self) -> MockResponse:
        db = load_local_db()
        mapped_table = self._map_table()
        
        if mapped_table not in db:
            db[mapped_table] = [] if mapped_table in ["challenges", "groups"] else {}

        collection = db[mapped_table]

        if self.operation == "select":
            items = []
            if isinstance(collection, dict):
                items = list(collection.values())
            else:
                items = collection

            filtered = []
            for r in items:
                match = True
                for f in self.filters:
                    try:
                        if not f(r):
                            match = False
                            break
                    except Exception:
                        match = False
                        break
                if match:
                    filtered.append(r)

            for col, desc in self.order_by:
                filtered.sort(key=lambda x: x.get(col) or "", reverse=desc)

            if self.offset_val > 0:
                filtered = filtered[self.offset_val:]
            if self.limit_val is not None:
                filtered = filtered[:self.limit_val]

            if self.is_single:
                if not filtered:
                    raise Exception("No rows found")
                return MockResponse(filtered[0])
            if self.is_maybe_single:
                return MockResponse(filtered[0] if filtered else None)
            return MockResponse(filtered)

        elif self.operation in ["insert", "upsert", "update"]:
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            inserted_items = []

            for p in payloads:
                item_id = p.get("id") or str(uuid.uuid4())
                item_record = dict(p)
                item_record["id"] = item_id

                if isinstance(collection, dict):
                    if self.operation == "update":
                        matching_keys = []
                        for k, r in collection.items():
                            match = True
                            for f in self.filters:
                                if not f(r):
                                    match = False
                                    break
                            if match:
                                matching_keys.append(k)
                        for k in matching_keys:
                            collection[k].update(p)
                            inserted_items.append(collection[k])
                    else:
                        collection[item_id] = item_record
                        inserted_items.append(item_record)
                else:
                    if self.operation == "update":
                        for r in collection:
                            match = True
                            for f in self.filters:
                                if not f(r):
                                    match = False
                                    break
                            if match:
                                r.update(p)
                                inserted_items.append(r)
                    else:
                        collection.append(item_record)
                        inserted_items.append(item_record)

            save_local_db(db)
            if self.is_single or self.is_maybe_single:
                return MockResponse(inserted_items[0] if inserted_items else None)
            return MockResponse(inserted_items)

        elif self.operation == "delete":
            deleted_items = []
            if isinstance(collection, dict):
                keys_to_delete = []
                for k, r in collection.items():
                    match = True
                    for f in self.filters:
                        try:
                            if not f(r):
                                match = False
                                break
                        except Exception:
                            match = False
                            break
                    if match:
                        keys_to_delete.append(k)
                        deleted_items.append(r)
                
                for k in keys_to_delete:
                    del collection[k]
            else:
                items_to_keep = []
                for r in collection:
                    match = True
                    for f in self.filters:
                        try:
                            if not f(r):
                                match = False
                                break
                        except Exception:
                            match = False
                            break
                    if match:
                        deleted_items.append(r)
                    else:
                        items_to_keep.append(r)
                db[mapped_table] = items_to_keep

            save_local_db(db)
            return MockResponse(deleted_items)

        return MockResponse(None)

class MockSupabaseClient:
    def __init__(self):
        self.auth = MockAuth()

    def from_(self, table: str) -> MockQueryBuilder:
        return MockQueryBuilder(table)

# ----------------- Inject Test Mocks into App modules -----------------
import app.database.supabase
app.database.supabase.supabase_client = MockSupabaseClient()

import app.services.nutrition.usda_service
mock_usda = MagicMock()
mock_usda.search_usda_food.return_value = {
    "food_name": "Idli",
    "calories": 98,
    "protein": 2.2,
    "carbs": 21.8,
    "fat": 0.3,
    "fiber": 0.9,
    "sodium": 30.0,
    "serving_size_g": 100.0,
    "source": "USDA"
}
app.services.nutrition.usda_service.usda_service = mock_usda

import app.services.nutrition.fatsecret_service
mock_fatsecret = MagicMock()
mock_fatsecret.search_branded_food.return_value = {
    "food_name": "Product 12345678",
    "calories": 180,
    "protein": 6.0,
    "carbs": 24.0,
    "fat": 5.0,
    "fiber": 1.5,
    "sodium": 150.0,
    "serving_size_g": 100.0,
    "source": "FatSecret"
}
app.services.nutrition.fatsecret_service.fatsecret_service = mock_fatsecret

# ----------------- Mock Gemini AI API Client -----------------
class MockGeminiResponse:
    def __init__(self, text):
        self.text = text

def mock_generate_content(prompt_or_list):
    if isinstance(prompt_or_list, list):
        return MockGeminiResponse(json.dumps({
            "meal_type": "Lunch",
            "estimated_total_weight": 420,
            "image_quality": "Good",
            "foods": [
                {
                    "name": "Chicken Biryani",
                    "food_name": "Chicken Biryani",
                    "weight_g": 350,
                    "confidence": 95,
                    "cooking_method": "Cooked",
                    "ingredients": ["Rice", "Chicken", "Spices", "Oil"]
                }
            ]
        }))
        
    prompt = str(prompt_or_list)
    if "healthy meal choice" in prompt:
        return MockGeminiResponse(json.dumps({"name": "Salmon Salad", "calories": 380, "protein": 32.0, "carbs": 8.0, "fats": 24.0}))
    elif "food description" in prompt:
        return MockGeminiResponse(json.dumps({"name": "Idli", "calories": 98, "protein": 2.2, "carbs": 21.8, "fats": 0.3}))
    elif "nutrition label" in prompt:
        return MockGeminiResponse(json.dumps({"name": "Nutrition Label Product", "calories": 250, "protein": 12.0, "carbs": 30.0, "fats": 8.0}))
    elif "UPC/barcode" in prompt:
        return MockGeminiResponse(json.dumps({"name": "Product 12345678", "calories": 180, "protein": 6.0, "carbs": 24.0, "fats": 5.0}))
    elif "user data" in prompt:
        return MockGeminiResponse("Fantastic effort! You've logged multiple workouts this week.")
    elif "daily health activity" in prompt:
        return MockGeminiResponse(json.dumps({
            "summary": "You had a highly active day, hitting your step goals.",
            "didBetter": "Great job meeting your water target.",
            "toImprove": "Try to focus on increasing your protein intake tomorrow."
        }))
    return MockGeminiResponse("{}")

mock_model = MagicMock()
mock_model.generate_content.side_effect = mock_generate_content

patcher = patch('google.generativeai.GenerativeModel', return_value=mock_model)
patcher.start()

# ----------------- Start FastAPI Client -----------------
from fastapi.testclient import TestClient
from app.main import app

try:
    client = TestClient(app)
except ImportError:
    print("TestClient requires httpx. Please install it.")
    sys.exit(1)


def run_tests():
    # Clear local storage on start to ensure clean test runs
    if os.path.exists(STORAGE_FILE):
        try:
            os.remove(STORAGE_FILE)
        except Exception:
            pass

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

    # 1a. Static Pages checks
    res = client.get("/privacy")
    assert_status(res, 200, "GET /privacy")
    res = client.get("/privacy.html")
    assert_status(res, 200, "GET /privacy.html")
    res = client.get("/delete-account")
    assert_status(res, 200, "GET /delete-account")
    res = client.get("/delete-account.html")
    assert_status(res, 200, "GET /delete-account.html")

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
    
    res = client.post("/api/nutrition/describe", json={"description": "2 eggs and toast"}, headers=headers)
    assert_status(res, 200, "POST /nutrition/describe")
    
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
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
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

    # 22. Workouts API: Log Workout
    workout_payload = {
        "workout_name": "Push Day",
        "date": "2026-06-26",
        "duration_seconds": 3600,
        "calories": 350,
        "workout_type": "strength",
        "category": "chest",
        "exercises": [
            {
                "name": "Bench Press",
                "sets": 3,
                "reps": 10,
                "weight": 60.0
            }
        ]
    }
    res = client.post("/api/workouts", json=workout_payload, headers=headers)
    is_workout_ok = assert_status(res, 200, "POST /workouts")
    
    # 23. Workouts API: Get Workouts
    res = client.get("/api/workouts", headers=headers)
    assert_status(res, 200, "GET /workouts")

    # 24. Fasting API: Start Fast
    fast_payload = {
        "protocol": "16-8"
    }
    res = client.post("/api/fasting/start", json=fast_payload, headers=headers)
    is_fast_ok = assert_status(res, 200, "POST /fasting/start")
    
    fast_id = ""
    if is_fast_ok:
        fast_id = res.json().get("data", {}).get("id", "")
    
    # 25. Fasting API: Get Active Fast
    res = client.get("/api/fasting/active", headers=headers)
    assert_status(res, 200, "GET /fasting/active")

    # 26. Fasting API: Stop Fast
    if is_fast_ok and fast_id:
        stop_payload = {
            "id": fast_id
        }
        res = client.post("/api/fasting/stop", json=stop_payload, headers=headers)
        assert_status(res, 200, "POST /fasting/stop")

    # 27. Groups & Challenges API: Get Groups
    res = client.get("/api/groups", headers=headers)
    assert_status(res, 200, "GET /groups")

    # 28. Groups & Challenges API: Get Challenges
    res = client.get("/api/challenges", headers=headers)
    assert_status(res, 200, "GET /challenges")

    # 29. Insights & Reports API: Get Insights
    res = client.get("/api/insights", headers=headers)
    assert_status(res, 200, "GET /insights")

    # 30. Insights & Reports API: Get Daily Report
    res = client.get("/api/insights/daily?date=2026-06-26", headers=headers)
    assert_status(res, 200, "GET /insights/daily")

    # 31. Supplements API: Add Supplement
    supp_payload = {
        "name": "Vitamin C",
        "dosage": "500mg",
        "time": "08:00"
    }
    res = client.post("/api/supplements", json=supp_payload, headers=headers)
    is_supp_ok = assert_status(res, 201, "POST /supplements")
    
    supp_id = ""
    if is_supp_ok:
        supp_id = res.json().get("id", "")
        
    # 32. Supplements API: Get Supplements
    res = client.get("/api/supplements", headers=headers)
    assert_status(res, 200, "GET /supplements")
    
    # 33. Supplements API: Delete Supplement
    if is_supp_ok and supp_id:
        res = client.delete(f"/api/supplements/{supp_id}", headers=headers)
        assert_status(res, 200, "DELETE /supplements/{id}")

    # 34. Referrals API: Get Referral Info (User 1)
    res = client.get("/api/referrals", headers=headers)
    is_ref_info_ok = assert_status(res, 200, "GET /referrals")
    user1_code = ""
    if is_ref_info_ok:
        user1_code = res.json().get("code")

    # 35. Referrals API: Create User 2 and Claim User 1's Code
    if user1_code:
        # Create second user
        client.post("/api/auth/signup", json={"email": "ref_friend@test.com", "password": "password123"})
        res = client.post("/api/auth/login", json={"email": "ref_friend@test.com", "password": "password123"})
        user2_token = res.json().get("token")
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        # Claim code
        res = client.post("/api/referrals/claim", json={"code": user1_code}, headers=user2_headers)
        assert_status(res, 200, "POST /referrals/claim (Claim user1 code)")
        
        # Verify stats updated for User 1
        res = client.get("/api/referrals", headers=headers)
        if assert_status(res, 200, "GET /referrals after claim"):
            data = res.json()
            assert data.get("points") == 100, f"Expected 100 points, got {data.get('points')}"
            assert len(data.get("referrals", [])) == 1, "Expected 1 referred friend"
            print("[PASS] Referrals stats and points verification passed.")

    # 36. User Search API
    res = client.get("/api/users/search?q=friend", headers=headers)
    assert_status(res, 200, "GET /users/search")

    # 37. Friends suggestions
    res = client.get("/api/friends/suggestions", headers=headers)
    assert_status(res, 200, "GET /friends/suggestions")

    # 38. Add friend
    res = client.post("/api/friends/add", json={"email": "ref_friend@test.com"}, headers=headers)
    assert_status(res, 200, "POST /friends/add")

    # 39. Friends list
    res = client.get("/api/friends", headers=headers)
    assert_status(res, 200, "GET /friends")

    # 40. Group Join, Leave & Messaging
    res = client.post("/api/groups", json={"name": "Test Run Group", "description": "Running group"}, headers=headers)
    assert_status(res, 200, "POST /groups")
    group_id = res.json()["data"]["id"]

    res = client.post(f"/api/groups/{group_id}/join", headers=headers)
    assert_status(res, 200, "POST /groups/{id}/join")

    res = client.post(f"/api/groups/{group_id}/messages", json={"message": "Hello group!"}, headers=headers)
    assert_status(res, 200, "POST /groups/{id}/messages")

    res = client.get(f"/api/groups/{group_id}/messages", headers=headers)
    assert_status(res, 200, "GET /groups/{id}/messages")

    res = client.post(f"/api/groups/{group_id}/leave", headers=headers)
    assert_status(res, 200, "POST /groups/{id}/leave")

    # 41. User Challenges & Join Challenge
    res = client.get("/api/challenges/user", headers=headers)
    assert_status(res, 200, "GET /challenges/user")

    res = client.post("/api/challenges/c123/join", headers=headers)
    assert_status(res, 200, "POST /challenges/{id}/join")

    # 42. Leaderboard API
    res = client.get("/api/leaderboard", headers=headers)
    assert_status(res, 200, "GET /leaderboard")

    # 43. Badges API
    res = client.get("/api/user/badges", headers=headers)
    assert_status(res, 200, "GET /user/badges")

    res = client.post("/api/user/badges", json={"badge_id": "First Log"}, headers=headers)
    assert_status(res, 200, "POST /user/badges")

    # 44. Nutrition Goals API
    res = client.get("/api/user/nutrition-goals", headers=headers)
    assert_status(res, 200, "GET /user/nutrition-goals")

    res = client.put("/api/user/nutrition-goals", json={"calorie_goal": 2200, "protein_goal": 150, "carbs_goal": 200, "fats_goal": 70}, headers=headers)
    assert_status(res, 200, "PUT /user/nutrition-goals")

    # 45. Supplement Take Log API
    res = client.post("/api/supplements/supp123/log?date=2026-08-03", headers=headers)
    assert_status(res, 200, "POST /supplements/{id}/log")

    res = client.get("/api/supplements/logs?date=2026-08-03", headers=headers)
    assert_status(res, 200, "GET /supplements/logs")

    # 46. Forgot Password
    res = client.post("/api/auth/forgot-password", json={"email": "test@example.com"})
    assert_status(res, 200, "POST /auth/forgot-password")
    data = res.json()
    assert data.get("success") == True, "[FAIL] forgot-password should return success"
    print("[PASS] POST /auth/forgot-password passed.")

    # 47. Direct Messages (DM)
    # Register a second user to DM
    res2 = client.post("/api/auth/signup", json={"email": "dmfriend@example.com", "password": "password123"})
    friend_token = res2.json().get("token") or res2.json().get("data", {}).get("token")
    friend_id_tmp = friend_token.replace("mock-token-", "") if friend_token else "friend123"

    res = client.post(f"/api/dm/{friend_id_tmp}", json={"message": "Hey, great workout!"}, headers=headers)
    assert_status(res, 200, "POST /dm/{friend_id}")

    res = client.get(f"/api/dm/{friend_id_tmp}", headers=headers)
    assert_status(res, 200, "GET /dm/{friend_id}")
    data = res.json()
    assert isinstance(data.get("data"), list), "[FAIL] DM messages should be a list"
    print("[PASS] GET /dm/{friend_id} messages returned correctly.")

    # 48. Challenge Invite
    res = client.post(f"/api/challenges/invite/{friend_id_tmp}", headers=headers)
    assert_status(res, 200, "POST /challenges/invite/{friend_id}")


    print("\n--- Test Results Summary ---")
    print(f"Total: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    run_tests()

