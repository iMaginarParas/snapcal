import os
import json
import random
import string
from datetime import datetime

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "data")
STORAGE_FILE = os.path.join(STORAGE_DIR, "storage.json")

class DbFallback:
    def __init__(self):
        self.db = {
            "users": {},
            "meals": {},
            "workouts": {},
            "dailyStats": {},
            "measurementLogs": {},
            "fastingLogs": {},
            "groups": [],
            "groupMembers": {},
            "groupMessages": {},
            "friendships": {},
            "challenges": [],
            "userChallenges": {},
            "userCorrections": {},  # Stores user corrections for AI learning
            "foods": {},
            "foodAliases": {},
            "nutritionCache": {},
            "barcodeCache": {},
            "favoriteFoods": {},
            "recentFoods": {},
            "mealTemplates": {},
            "dailySteps": {},
            "profiles": {},
            "weightHistory": {}
        }
        self.init_db()

    def init_db(self):
        if not os.path.exists(STORAGE_DIR):
            os.makedirs(STORAGE_DIR, exist_ok=True)
        if os.path.exists(STORAGE_FILE):
            try:
                with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for key in self.db.keys():
                        if key in loaded:
                            self.db[key] = loaded[key]
                
                # Check for default challenge
                if not self.db.get("challenges"):
                    self.db["challenges"] = [{
                        "id": "default_challenge_core_crusher",
                        "title": "7-Day Core Crusher",
                        "description": "Complete 5 core workouts this week to earn the exclusive Golden Abs badge.",
                        "target_workouts": 5,
                        "points": 500,
                        "created_at": datetime.utcnow().isoformat() + "Z"
                    }]
                    self.save_db()
            except Exception as e:
                print(f"Failed to parse storage.json: {e}. Initializing empty.")
        else:
            self.save_db()

    def save_db(self):
        try:
            with open(STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.db, f, indent=2)
        except Exception as e:
            print(f"Failed to write to storage.json: {e}")

    def generate_id(self, length=9):
        chars = string.ascii_lowercase + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    # --- Users ---
    def get_user(self, user_id: str):
        if user_id not in self.db["users"]:
            default_username = user_id.lower().replace("@", "_").replace(".", "_")
            self.db["users"][user_id] = {
                "id": user_id,
                "email": f"{user_id}@fallback.local",
                "username": default_username,
                "name": "Guest User",
                "age": None,
                "weight": None,
                "height": None,
                "goals": None,
                "profile_picture_url": None
            }
            self.save_db()
        return self.db["users"][user_id]

    def update_user(self, user_id: str, updates: dict):
        user = self.get_user(user_id)
        if "username" in updates and updates["username"] != user["username"]:
            username_exists = any(
                uid != user_id and self.db["users"][uid].get("username", "").lower() == updates["username"].lower()
                for uid in self.db["users"]
            )
            if username_exists:
                raise ValueError("Username is already taken")
        
        user.update(updates)
        self.db["users"][user_id] = user
        self.save_db()
        return user

    def get_all_users(self):
        return list(self.db["users"].values())

    # --- Meals & Food Items ---
    def get_meals(self, user_id: str):
        return self.db["meals"].get(user_id, [])

    def add_meal(self, user_id: str, meal: dict):
        if user_id not in self.db["meals"]:
            self.db["meals"][user_id] = []
        
        meal_id = meal.get("id") or self.generate_id()
        new_meal = {
            "id": meal_id,
            "user_id": user_id,
            "name": meal.get("name") or "Logged Meal",
            "total_calories": int(meal.get("total_calories") or meal.get("calories") or 0),
            "protein": float(meal.get("protein") or 0.0),
            "carbs": float(meal.get("carbs") or 0.0),
            "fat": float(meal.get("fat") or meal.get("fats") or 0.0),
            "fiber": float(meal.get("fiber") or 0.0),
            "image_url": meal.get("image_url") or None,
            "description": meal.get("description") or None,
            "logged_at": meal.get("logged_at") or datetime.utcnow().isoformat() + "Z",
            "food_items": meal.get("food_items") or []  # List of child items
        }
        self.db["meals"][user_id].append(new_meal)
        self.save_db()
        return new_meal

    # --- Workouts ---
    def get_workouts(self, user_id: str):
        return self.db["workouts"].get(user_id, [])

    def add_workout(self, user_id: str, workout: dict):
        if user_id not in self.db["workouts"]:
            self.db["workouts"][user_id] = []
        
        new_workout = {
            "id": self.generate_id(),
            "user_id": user_id,
            "workout_name": workout["workout_name"],
            "distance": float(workout.get("distance") or 0.0),
            "duration_seconds": int(workout.get("duration_seconds") or 0),
            "calories": int(workout.get("calories") or 0),
            "route_points": workout.get("route_points") or [],
            "workout_type": workout.get("workout_type") or "cardio",
            "category": workout.get("category") or None,
            "exercises": workout.get("exercises") or None,
            "completed": True,
            "completed_at": workout.get("completed_at") or datetime.utcnow().isoformat() + "Z"
        }
        self.db["workouts"][user_id].append(new_workout)
        self.save_db()
        return new_workout

    def delete_workout(self, user_id: str, id: str):
        if user_id not in self.db["workouts"]:
            return False
        initial_len = len(self.db["workouts"][user_id])
        self.db["workouts"][user_id] = [w for w in self.db["workouts"][user_id] if w["id"] != id]
        if len(self.db["workouts"][user_id]) < initial_len:
            self.save_db()
            return True
        return False

    # --- Daily Stats ---
    def get_daily_stats(self, user_id: str, date_str: str):
        if user_id not in self.db["dailyStats"]:
            self.db["dailyStats"][user_id] = {}
        if date_str not in self.db["dailyStats"][user_id]:
            self.db["dailyStats"][user_id][date_str] = {
                "id": self.generate_id(),
                "user_id": user_id,
                "date": date_str,
                "steps": 0,
                "water_ml": 0
            }
            self.save_db()
        return self.db["dailyStats"][user_id][date_str]

    def update_daily_stats(self, user_id: str, date_str: str, updates: dict):
        stats = self.get_daily_stats(user_id, date_str)
        if "steps" in updates and updates["steps"] is not None:
            stats["steps"] = updates["steps"]
        if "water_ml" in updates and updates["water_ml"] is not None:
            stats["water_ml"] = updates["water_ml"]
        self.db["dailyStats"][user_id][date_str] = stats
        self.save_db()
        return stats

    # --- Measurements ---
    def get_measurements(self, user_id: str, metric_type: str = None):
        logs = self.db["measurementLogs"].get(user_id, [])
        if metric_type:
            return [l for l in logs if l["metric_type"] == metric_type]
        return sorted(logs, key=lambda x: x["logged_at"], reverse=True)

    def add_measurement(self, user_id: str, metric: dict):
        if user_id not in self.db["measurementLogs"]:
            self.db["measurementLogs"][user_id] = []
        
        now = datetime.utcnow()
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        formatted_date = metric.get("date") or f"{months[now.month-1]} {str(now.day).zfill(2)}, {now.year}"
        
        new_metric = {
            "id": self.generate_id(),
            "user_id": user_id,
            "metric_type": metric["metric_type"],
            "value": float(metric["value"]),
            "logged_at": now.isoformat() + "Z",
            "date": formatted_date
        }
        self.db["measurementLogs"][user_id].append(new_metric)
        self.save_db()
        return new_metric

    def delete_measurement(self, user_id: str, id: str):
        if user_id not in self.db["measurementLogs"]:
            return False
        initial_len = len(self.db["measurementLogs"][user_id])
        self.db["measurementLogs"][user_id] = [m for m in self.db["measurementLogs"][user_id] if m["id"] != id]
        if len(self.db["measurementLogs"][user_id]) < initial_len:
            self.save_db()
            return True
        return False

    # --- Fasting ---
    def get_active_fast(self, user_id: str):
        logs = self.db["fastingLogs"].get(user_id, [])
        for f in logs:
            if not f.get("completed"):
                return f
        return None

    def start_fast(self, user_id: str, protocol: str):
        if user_id not in self.db["fastingLogs"]:
            self.db["fastingLogs"][user_id] = []
        active = self.get_active_fast(user_id)
        if active:
            return active
        
        new_fast = {
            "id": self.generate_id(),
            "user_id": user_id,
            "protocol": protocol,
            "start_time": datetime.utcnow().isoformat() + "Z",
            "completed": False
        }
        self.db["fastingLogs"][user_id].append(new_fast)
        self.save_db()
        return new_fast

    def stop_fast(self, user_id: str, id: str):
        if user_id not in self.db["fastingLogs"]:
            return None
        for f in self.db["fastingLogs"][user_id]:
            if f["id"] == id:
                f["completed"] = True
                f["end_time"] = datetime.utcnow().isoformat() + "Z"
                self.save_db()
                return f
        return None

    def get_fasting_history(self, user_id: str):
        logs = self.db["fastingLogs"].get(user_id, [])
        completed = [f for f in logs if f.get("completed")]
        return sorted(completed, key=lambda x: x.get("end_time", ""), reverse=True)

    # --- Groups ---
    def get_groups(self, user_id: str):
        if not self.db.get("groups"):
            self.db["groups"] = [
                { "id": "g_fitness_workouts", "name": "Fitness & Workouts", "description": "Share daily workouts that match your calorie goals, keep each other accountable.", "is_public": True, "created_by": "system", "created_at": datetime.utcnow().isoformat() + "Z" },
                { "id": "g_new_calorie", "name": "New to Calorie Tracking", "description": "Beginner questions, quick meal tips, tracking shortcuts, and celebrating first wins.", "is_public": True, "created_by": "system", "created_at": datetime.utcnow().isoformat() + "Z" },
                { "id": "g_muscle_gain", "name": "Muscle Gain & Bulking", "description": "Strategies for eating in a clean surplus, protein recipes, and heavy weight lifting.", "is_public": True, "created_by": "system", "created_at": datetime.utcnow().isoformat() + "Z" },
                { "id": "g_clean_fasting", "name": "Clean Fasting Habits", "description": "Share your intermittent fasting protocols, water fasting tips, and support.", "is_public": True, "created_by": "system", "created_at": datetime.utcnow().isoformat() + "Z" }
            ]
            self.db["groupMembers"]["g_fitness_workouts"] = ["system", "JD", "RS", "A"]
            self.db["groupMembers"]["g_new_calorie"] = ["system", "M", "TL", "BK"]
            self.db["groupMembers"]["g_muscle_gain"] = ["system", "P", "SO", "D"]
            self.db["groupMembers"]["g_clean_fasting"] = ["system", "E", "W", "CH"]
            self.save_db()

        result = []
        for g in self.db["groups"]:
            members = self.db["groupMembers"].get(g["id"]) or []
            if g["is_public"] or g["created_by"] == user_id or user_id in members:
                avatars = []
                for mid in members[:3]:
                    if mid == "system":
                        avatars.append("SYS")
                    else:
                        u = self.db["users"].get(mid)
                        avatars.append("".join([e[0] for e in (u.get("name") or "US").split(" ") if e]).upper()[:2] if u else "US")
                
                result.append({
                    "id": g["id"],
                    "name": g["name"],
                    "description": g["description"],
                    "is_public": g["is_public"],
                    "created_by": g["created_by"],
                    "memberCount": len(members),
                    "isJoined": user_id in members,
                    "avatars": avatars,
                    "extraMemberText": f"+{len(members) - 3}" if len(members) > 3 else "",
                    "tag": "Trending" if g["created_by"] == "system" else "New"
                })
        return result

    def create_group(self, user_id: str, group: dict):
        new_gp = {
            "id": self.generate_id(),
            "name": group["name"],
            "description": group.get("description") or None,
            "is_public": group.get("is_public") is not False,
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        if "groups" not in self.db:
            self.db["groups"] = []
        self.db["groups"].append(new_gp)
        self.db["groupMembers"][new_gp["id"]] = [user_id]
        self.save_db()
        return {
            **new_gp,
            "memberCount": 1,
            "isJoined": True,
            "avatars": ["ME"],
            "extraMemberText": "",
            "tag": "New"
        }

    def join_group(self, user_id: str, group_id: str):
        if group_id not in self.db["groupMembers"]:
            self.db["groupMembers"][group_id] = []
        if user_id not in self.db["groupMembers"][group_id]:
            self.db["groupMembers"][group_id].append(user_id)
            self.save_db()
        
        group = next((g for g in self.db["groups"] if g["id"] == group_id), None)
        return {
            **group,
            "memberCount": len(self.db["groupMembers"][group_id]),
            "isJoined": True
        } if group else None

    def leave_group(self, user_id: str, group_id: str):
        if group_id in self.db["groupMembers"]:
            self.db["groupMembers"][group_id] = [mid for mid in self.db["groupMembers"][group_id] if mid != user_id]
            self.save_db()
        
        group = next((g for g in self.db["groups"] if g["id"] == group_id), None)
        return {
            **group,
            "memberCount": len(self.db["groupMembers"].get(group_id, [])),
            "isJoined": False
        } if group else None

    # --- Group Messages ---
    def get_group_messages(self, group_id: str):
        return self.db["groupMessages"].get(group_id, [])

    def send_group_message(self, user_id: str, group_id: str, message: str):
        if group_id not in self.db["groupMessages"]:
            self.db["groupMessages"][group_id] = []
        user = self.get_user(user_id)
        new_msg = {
            "id": self.generate_id(),
            "group_id": group_id,
            "user_id": user_id,
            "message": message,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "sender_name": user.get("name") or "Guest User"
        }
        self.db["groupMessages"][group_id].append(new_msg)
        self.save_db()
        return new_msg

    # --- Friends & Leaderboard ---
    def get_friends(self, user_id: str):
        if user_id not in self.db["friendships"] or len(self.db["friendships"][user_id]) == 0:
            self.db["friendships"][user_id] = []
            default_friends = [
                { "id": "f_sarah", "name": "Sarah Miller", "email": "sarah.m@fitflow.ai" },
                { "id": "f_alex", "name": "Alex Johnson", "email": "alex.j@fitflow.ai" },
                { "id": "f_john", "name": "John Doe", "email": "john.d@fitflow.ai" },
                { "id": "f_emma", "name": "Emma Wilson", "email": "emma.w@fitflow.ai" }
            ]
            for df in default_friends:
                self.db["users"][df["id"]] = {
                    "id": df["id"],
                    "email": df["email"],
                    "name": df["name"],
                    "age": 25,
                    "weight": 70.0,
                    "height": 170.0,
                    "goals": "Stay Healthy",
                    "profile_picture_url": None
                }
                today_str = datetime.utcnow().isoformat().split("T")[0]
                if df["id"] not in self.db["dailyStats"]:
                    self.db["dailyStats"][df["id"]] = {}
                self.db["dailyStats"][df["id"]][today_str] = {
                    "id": self.generate_id(),
                    "user_id": df["id"],
                    "date": today_str,
                    "steps": 5000 + random.randint(0, 6000),
                    "water_ml": 1500
                }
                
                self.db["friendships"][user_id].append({
                    "id": self.generate_id(),
                    "user_id": user_id,
                    "friend_id": df["id"],
                    "status": "accepted",
                    "created_at": datetime.utcnow().isoformat() + "Z"
                })
            self.save_db()

        result = []
        for f in self.db["friendships"].get(user_id, []):
            friend_user = self.get_user(f["friend_id"])
            today_str = datetime.utcnow().isoformat().split("T")[0]
            stats = self.get_daily_stats(f["friend_id"], today_str)
            steps = stats.get("steps") or 0
            
            result.append({
                "id": f["id"],
                "friend_id": f["friend_id"],
                "name": friend_user.get("name") or "Friend User",
                "email": friend_user.get("email") or "",
                "steps": steps,
                "calories": int(steps * 0.045),
                "avatar": "".join([e[0] for e in (friend_user.get("name") or "FR").split(" ") if e]).upper()[:2],
                "status": "Active"
            })
        return result

    def add_friend_by_email(self, user_id: str, email: str):
        search_val = email.strip().lower()
        friend_id = next((uid for uid, u in self.db["users"].items() if u.get("email", "").lower() == search_val or u.get("name", "").lower() == search_val), None)
        
        if not friend_id:
            mock_id = search_val.replace("@", "_").replace(".", "_")
            is_email = "@" in search_val
            mock_email = search_val if is_email else f"{search_val}@sabtrack.com"
            mock_name = search_val.split("@")[0].upper() if is_email else search_val.upper()
            
            self.db["users"][mock_id] = {
                "id": mock_id,
                "email": mock_email,
                "name": mock_name,
                "age": 25,
                "weight": 70.0,
                "height": 170.0,
                "goals": "Stay Healthy",
                "profile_picture_url": None
            }
            self.save_db()
            friend_id = mock_id
            
        return self.create_friendship(user_id, friend_id)

    def create_friendship(self, user_id: str, friend_id: str):
        if user_id not in self.db["friendships"]:
            self.db["friendships"][user_id] = []
        if friend_id not in self.db["friendships"]:
            self.db["friendships"][friend_id] = []
            
        if any(f["friend_id"] == friend_id for f in self.db["friendships"][user_id]):
            return None

        now_str = datetime.utcnow().isoformat() + "Z"
        new_f1 = {
            "id": self.generate_id(),
            "user_id": user_id,
            "friend_id": friend_id,
            "status": "accepted",
            "created_at": now_str
        }
        self.db["friendships"][user_id].append(new_f1)
        
        new_f2 = {
            "id": self.generate_id(),
            "user_id": friend_id,
            "friend_id": user_id,
            "status": "accepted",
            "created_at": now_str
        }
        self.db["friendships"][friend_id].append(new_f2)
        
        self.save_db()
        return new_f1

    def get_weekly_points(self, user_id: str):
        today_str = datetime.utcnow().isoformat().split("T")[0]
        stats = self.get_daily_stats(user_id, today_str)
        workouts = self.get_workouts(user_id)
        workouts_count = len(workouts)
        points = int(stats.get("steps", 0) * 0.1 + stats.get("water_ml", 0) * 0.05 + workouts_count * 100)
        return points

    # --- Challenges ---
    def get_challenges(self):
        return self.db.get("challenges", [])

    def get_user_challenges(self, user_id: str):
        logs = self.db["userChallenges"].get(user_id, [])
        result = []
        for uc in logs:
            ch = next((c for c in self.db["challenges"] if c["id"] == uc["challenge_id"]), None)
            result.append({
                **uc,
                "challenge": ch
            })
        return result

    def join_challenge(self, user_id: str, challenge_id: str):
        if user_id not in self.db["userChallenges"]:
            self.db["userChallenges"][user_id] = []
        
        existing = next((uc for uc in self.db["userChallenges"][user_id] if uc["challenge_id"] == challenge_id), None)
        if existing:
            return existing
            
        new_uc = {
            "id": self.generate_id(),
            "user_id": user_id,
            "challenge_id": challenge_id,
            "completed_workouts": 2,
            "completed": False,
            "joined_at": datetime.utcnow().isoformat() + "Z"
        }
        self.db["userChallenges"][user_id].append(new_uc)
        self.save_db()
        return new_uc

    def update_challenge_progress(self, user_id: str, challenge_id: str):
        if user_id not in self.db["userChallenges"]:
            return None
        
        uc = next((u for u in self.db["userChallenges"][user_id] if u["challenge_id"] == challenge_id), None)
        if uc:
            ch = next((c for c in self.db["challenges"] if c["id"] == challenge_id), None)
            target = ch["target_workouts"] if ch else 5
            uc["completed_workouts"] = min(target, uc["completed_workouts"] + 1)
            if uc["completed_workouts"] >= target:
                uc["completed"] = True
            self.save_db()
        return uc

    # --- User Corrections (Learning System) ---
    def add_correction(self, user_id: str, original_name: str, corrected_name: str):
        if user_id not in self.db["userCorrections"]:
            self.db["userCorrections"][user_id] = []
        
        orig = original_name.strip().lower()
        corr = corrected_name.strip().lower()

        exists = any(c["original_name"].lower() == orig and c["corrected_name"].lower() == corr 
                     for c in self.db["userCorrections"][user_id])
        
        if not exists:
            self.db["userCorrections"][user_id].append({
                "id": self.generate_id(),
                "original_name": original_name,
                "corrected_name": corrected_name,
                "created_at": datetime.utcnow().isoformat() + "Z"
            })
            self.save_db()

    def get_corrections(self, user_id: str):
        return self.db["userCorrections"].get(user_id, [])

    # --- Profiles & Calculations ---
    def get_profile(self, user_id: str):
        return self.db["profiles"].get(user_id)

    def update_profile(self, user_id: str, profile: dict):
        self.db["profiles"][user_id] = profile
        self.save_db()
        return profile

    def add_weight_history(self, user_id: str, weight: float, bmi: float):
        if user_id not in self.db["weightHistory"]:
            self.db["weightHistory"][user_id] = []
        entry = {
            "id": self.generate_id(),
            "user_id": user_id,
            "weight": weight,
            "bmi": bmi,
            "recorded_at": datetime.utcnow().isoformat() + "Z"
        }
        self.db["weightHistory"][user_id].append(entry)
        self.save_db()
        return entry

    def get_weight_history(self, user_id: str):
        return self.db["weightHistory"].get(user_id, [])

fallback_db = DbFallback()

