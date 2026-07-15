from typing import Dict, Any, List, Optional
from app.database.supabase import supabase_client, is_supabase_live
from app.database.fallback import fallback_db
from datetime import datetime
import uuid

class DBRepository:
    """Centralized database repository handling all Supabase and fallback queries."""

    # --- Users & Profiles ---
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_user(user_id)
        res = supabase_client.from_("users").select("*").eq("id", user_id).single().execute()
        return res.data if res else None

    def create_user_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            fallback_db.update_user(profile["id"], profile)
            return profile
        res = supabase_client.from_("users").insert(profile).execute()
        return res.data[0] if res and res.data else {}

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.update_user(user_id, updates)
        res = supabase_client.from_("users").update(updates).eq("id", user_id).execute()
        return res.data[0] if res and res.data else {}

    def check_username_exists(self, username: str, exclude_user_id: str) -> bool:
        if not is_supabase_live():
            return False # Fallback doesn't strictly enforce unique usernames for now
        res = supabase_client.from_("users").select("id").eq("username", username).neq("id", exclude_user_id).execute()
        return bool(res.data)

    def get_calculated_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_profile(user_id)
        res = supabase_client.from_("profiles").select("*").eq("user_id", user_id).maybe_single().execute()
        return res.data if res else None

    def upsert_calculated_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        profile_data["user_id"] = user_id
        if not is_supabase_live():
            return fallback_db.update_profile(user_id, profile_data)
        res = supabase_client.from_("profiles").upsert(profile_data).execute()
        return res.data[0] if res and res.data else {}

    def add_weight_history_entry(self, user_id: str, weight: float, bmi: float) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.add_weight_history(user_id, weight, bmi)
        payload = {
            "user_id": user_id,
            "weight": weight,
            "bmi": bmi
        }
        res = supabase_client.from_("weight_history").insert(payload).execute()
        return res.data[0] if res and res.data else {}

    def get_weight_history_records(self, user_id: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_weight_history(user_id)
        res = supabase_client.from_("weight_history").select("*").eq("user_id", user_id).order("recorded_at", desc=False).execute()
        return res.data if res else []


    # --- Workouts ---
    def get_workouts(self, user_id: str, date: Optional[str] = None, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            workouts = fallback_db.get_workouts(user_id)
            if date:
                workouts = [w for w in workouts if w.get("completed_at", "").split("T")[0] == date]
            return workouts[offset: offset + limit]
            
        query = supabase_client.from_("workouts").select("*").eq("user_id", user_id)
        if date:
            query = query.gte("completed_at", f"{date}T00:00:00.000Z").lte("completed_at", f"{date}T23:59:59.999Z")
        res = query.order("completed_at", desc=True).range(offset, offset + limit - 1).execute()
        return res.data if res else []

    def create_workout(self, user_id: str, workout_data: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.add_workout(user_id, workout_data)
        res = supabase_client.from_("workouts").insert(workout_data).execute()
        return res.data[0] if res and res.data else {}

    def delete_workout(self, user_id: str, workout_id: str) -> bool:
        if not is_supabase_live():
            return fallback_db.delete_workout(user_id, workout_id)
        res = supabase_client.from_("workouts").delete().eq("id", workout_id).eq("user_id", user_id).execute()
        return bool(res.data) if res else False

    # --- Daily Stats ---
    def get_daily_stats(self, user_id: str, date_str: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_daily_stats(user_id, date_str)
        res = supabase_client.from_("daily_stats").select("*").eq("user_id", user_id).eq("date", date_str).maybe_single().execute()
        return res.data if res else None

    def create_daily_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.update_daily_stats(stats["user_id"], stats["date"], stats)
        res = supabase_client.from_("daily_stats").insert(stats).execute()
        return res.data[0] if res and res.data else {}

    def update_daily_stats(self, user_id: str, date_str: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.update_daily_stats(user_id, date_str, updates)
        res = supabase_client.from_("daily_stats").update(updates).eq("user_id", user_id).eq("date", date_str).execute()
        return res.data[0] if res and res.data else {}

    # --- Measurements ---
    def get_measurements(self, user_id: str, metric_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_measurements(user_id, metric_type)
        query = supabase_client.from_("measurement_logs").select("*").eq("user_id", user_id)
        if metric_type:
            query = query.eq("metric_type", metric_type)
        res = query.order("logged_at", desc=True).execute()
        return res.data

    def log_measurement(self, user_id: str, measurement: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.add_measurement(user_id, measurement)
        res = supabase_client.from_("measurement_logs").insert(measurement).execute()
        return res.data[0] if res and res.data else {}

    def delete_measurement(self, user_id: str, measurement_id: str) -> bool:
        if not is_supabase_live():
            return fallback_db.delete_measurement(user_id, measurement_id)
        res = supabase_client.from_("measurement_logs").delete().eq("id", measurement_id).eq("user_id", user_id).execute()
        return bool(res.data) if res else False

    # --- Fasting Logs ---
    def get_active_fast(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_active_fast(user_id)
        res = supabase_client.from_("fasting_logs").select("*").eq("user_id", user_id).eq("completed", False).maybe_single().execute()
        return res.data if res else None

    def start_fast(self, user_id: str, protocol: str) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.start_fast(user_id, protocol)
        db_payload = {
            "user_id": user_id,
            "protocol": protocol,
            "start_time": datetime.utcnow().isoformat() + "Z",
            "completed": False
        }
        res = supabase_client.from_("fasting_logs").insert(db_payload).execute()
        return res.data[0] if res and res.data else {}

    def stop_fast(self, user_id: str, fast_id: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.stop_fast(user_id, fast_id)
        db_payload = {
            "completed": True,
            "end_time": datetime.utcnow().isoformat() + "Z"
        }
        res = supabase_client.from_("fasting_logs").update(db_payload).eq("id", fast_id).eq("user_id", user_id).execute()
        return res.data[0] if res and res.data else None

    # --- Meals & Food ---
    def get_meals(self, user_id: str, date_str: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return [m for m in fallback_db.get_meals(user_id) if m.get("logged_at", "").split("T")[0] == date_str]
        res = supabase_client.from_("meals").select("*, food_items(*)").eq("user_id", user_id).gte("logged_at", f"{date_str}T00:00:00.000Z").lte("logged_at", f"{date_str}T23:59:59.999Z").execute()
        return res.data if res else []

    def create_meal(self, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.add_meal(meal_data["user_id"], meal_data)
        res = supabase_client.from_("meals").insert(meal_data).execute()
        return res.data[0] if res and res.data else {}

    def create_food_items(self, food_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return food_items # Handled in fallback_db.add_meal implicitly
        res = supabase_client.from_("food_items").insert(food_items).execute()
        return res.data

    # --- Groups & Challenges ---
    def get_groups(self, user_id: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_groups(user_id)
        res = supabase_client.from_("groups").select("*").execute()
        return res.data if res else []

    def create_group(self, group_data: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.add_group(group_data)
        res = supabase_client.from_("groups").insert(group_data).execute()
        return res.data[0] if res and res.data else {}

    def get_challenges(self) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_challenges()
        res = supabase_client.from_("challenges").select("*").execute()
        return res.data if res else []

    def get_user_challenge(self, user_id: str, challenge_id: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return None # Not strictly implemented in fallback easily
        res = supabase_client.from_("user_challenges").select("*").eq("user_id", user_id).eq("challenge_id", challenge_id).maybe_single().execute()
        return res.data if res else None

    def create_user_challenge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return data
        res = supabase_client.from_("user_challenges").insert(data).execute()
        return res.data[0] if res and res.data else {}

    def update_user_challenge(self, challenge_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return updates
        res = supabase_client.from_("user_challenges").update(updates).eq("id", challenge_id).execute()
        return res.data[0] if res and res.data else {}

    # --- Supplements ---
    def get_supplements(self, user_id: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_supplements(user_id)
        res = supabase_client.from_("supplements").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
        return res.data if res else []

    def add_supplement(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        data["user_id"] = user_id
        if not is_supabase_live():
            return fallback_db.add_supplement(user_id, data)
        res = supabase_client.from_("supplements").insert(data).execute()
        return res.data[0] if res and res.data else {}

    def delete_supplement(self, user_id: str, supplement_id: str) -> bool:
        if not is_supabase_live():
            return fallback_db.delete_supplement(user_id, supplement_id)
        res = supabase_client.from_("supplements").delete().eq("id", supplement_id).eq("user_id", user_id).execute()
        return bool(res.data) if res else False

    # --- Referrals ---
    def get_referral_info(self, user_id: str) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.get_referral_info(user_id)
            
        # 1. Fetch user's own referral code & referred_by
        user_res = supabase_client.from_("users").select("referral_code, referred_by").eq("id", user_id).single().execute()
        user_data = user_res.data if user_res else None
        
        code = ""
        if user_data:
            code = user_data.get("referral_code") or ""
            
        # 2. If code doesn't exist, generate one and update it
        if not code:
            import string, random
            chars = string.ascii_uppercase + string.digits
            code = "FIT-" + "".join(random.choice(chars) for _ in range(6))
            supabase_client.from_("users").update({"referral_code": code}).eq("id", user_id).execute()
            
        # 3. Query all users referred by this user
        ref_res = supabase_client.from_("users").select("id, name, email").eq("referred_by", user_id).execute()
        referred_users = []
        if ref_res and ref_res.data:
            for u in ref_res.data:
                referred_users.append({
                    "id": str(u.get("id")),
                    "name": u.get("name") or "Friend",
                    "email": u.get("email") or ""
                })
                
        # 100 points per referral
        points = len(referred_users) * 100
        
        return {
            "code": code,
            "referrals": referred_users,
            "points": points
        }

    def claim_referral_code(self, user_id: str, code: str) -> bool:
        if not is_supabase_live():
            return fallback_db.claim_referral_code(user_id, code)
            
        clean_code = code.strip().upper()
        
        # 1. Check if user already claimed a code
        user_res = supabase_client.from_("users").select("referred_by").eq("id", user_id).single().execute()
        user_data = user_res.data if user_res else None
        if user_data and user_data.get("referred_by"):
            raise ValueError("You have already claimed a referral code")
            
        # 2. Find owner of the code
        owner_res = supabase_client.from_("users").select("id").eq("referral_code", clean_code).execute()
        if not owner_res or not owner_res.data:
            raise ValueError("Invalid referral code")
            
        owner_id = owner_res.data[0]["id"]
        if str(owner_id) == str(user_id):
            raise ValueError("Cannot claim your own referral code")
            
        # 3. Update current user's referred_by
        supabase_client.from_("users").update({"referred_by": owner_id}).eq("id", user_id).execute()
        
        # 4. Record the referral in the referrals table
        referral_payload = {
            "referrer_id": owner_id,
            "referred_id": user_id,
            "code_used": clean_code
        }
        supabase_client.from_("referrals").insert(referral_payload).execute()
        
        return True

    # --- Friends ---
    def get_friends(self, user_id: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_friends(user_id)
            
        try:
            res = supabase_client.from_("friendships").select("id, status, friend_id, users!friend_id(id, name, email, username, profile_picture_url)").eq("user_id", user_id).execute()
            data = res.data
        except Exception:
            try:
                res = supabase_client.from_("friendships").select("id, status, friend_id").eq("user_id", user_id).execute()
                data = res.data
                # Fetch users manually
                for item in data:
                    uid = item["friend_id"]
                    user_res = supabase_client.from_("users").select("id, name, email, username, profile_picture_url").eq("id", uid).single().execute()
                    item["users"] = user_res.data if user_res else {}
            except Exception:
                data = []

        result = []
        if data:
            for f in data:
                # Use users key from join or custom fetched
                friend_user = f.get("users") or f.get("friend") or {}
                fid = f.get("friend_id") or friend_user.get("id")
                if not fid:
                    continue
                
                # Get daily stats for the friend
                today_str = datetime.utcnow().isoformat().split("T")[0]
                steps = 0
                try:
                    stats_res = supabase_client.from_("daily_stats").select("steps").eq("user_id", fid).eq("date", today_str).maybe_single().execute()
                    if stats_res and stats_res.data:
                        steps = stats_res.data.get("steps") or 0
                except Exception:
                    pass
                    
                result.append({
                    "id": str(f.get("id")),
                    "friend_id": str(fid),
                    "name": friend_user.get("name") or "Friend User",
                    "email": friend_user.get("email") or "",
                    "steps": steps,
                    "calories": int(steps * 0.045),
                    "avatar": "".join([e[0] for e in (friend_user.get("name") or "FR").split(" ") if e]).upper()[:2],
                    "status": "Active"
                })
        return result

    def get_friend_suggestions(self, user_id: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            all_users = fallback_db.get_all_users()
            friends = fallback_db.get_friends(user_id)
            friend_ids = {str(f["friend_id"]) for f in friends}
            friend_ids.add(str(user_id))
            
            suggestions = []
            for u in all_users:
                uid_str = str(u["id"])
                if uid_str not in friend_ids:
                    suggestions.append({
                        "id": uid_str,
                        "name": u.get("name") or "User",
                        "username": u.get("username") or "",
                        "email": u.get("email") or "",
                        "profile_picture_url": u.get("profile_picture_url")
                    })
            return suggestions[:5]
            
        try:
            friends_res = supabase_client.from_("friendships").select("friend_id").eq("user_id", user_id).execute()
            friend_ids = {str(f["friend_id"]) for f in friends_res.data} if (friends_res and friends_res.data) else set()
            friend_ids.add(str(user_id))
            
            users_res = supabase_client.from_("users").select("id, name, email, username, profile_picture_url").limit(20).execute()
            suggestions = []
            if users_res and users_res.data:
                for u in users_res.data:
                    uid_str = str(u["id"])
                    if uid_str not in friend_ids:
                        suggestions.append({
                            "id": uid_str,
                            "name": u.get("name") or "User",
                            "username": u.get("username") or "",
                            "email": u.get("email") or "",
                            "profile_picture_url": u.get("profile_picture_url")
                        })
            return suggestions[:5]
        except Exception:
            return []

    def add_friend(self, user_id: str, identifier: str) -> Dict[str, Any]:
        if not is_supabase_live():
            res = fallback_db.add_friend_by_email(user_id, identifier)
            return res if res else {}
            
        user_res = supabase_client.from_("users").select("id, email, name").or_(f"email.eq.{identifier},username.eq.{identifier}").execute()
        friend_user = user_res.data[0] if (user_res and user_res.data) else None
        
        if not friend_user:
            raise ValueError("User not found")
            
        friend_id = friend_user["id"]
        if str(friend_id) == str(user_id):
            raise ValueError("Cannot add yourself as a friend")
            
        existing = supabase_client.from_("friendships").select("id").eq("user_id", user_id).eq("friend_id", friend_id).maybe_single().execute()
        if existing and existing.data:
            return existing.data
            
        f1 = {"user_id": user_id, "friend_id": friend_id, "status": "accepted"}
        f2 = {"user_id": friend_id, "friend_id": user_id, "status": "accepted"}
        
        supabase_client.from_("friendships").insert([f1, f2]).execute()
        return f1

    def search_users(self, query: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            q = query.strip().lower()
            all_users = fallback_db.get_all_users()
            results = []
            for u in all_users:
                name = (u.get("name") or "").lower()
                username = (u.get("username") or "").lower()
                email = (u.get("email") or "").lower()
                if q in name or q in username or q in email:
                    results.append({
                        "id": str(u["id"]),
                        "name": u.get("name") or "User",
                        "username": u.get("username") or "",
                        "email": u.get("email") or "",
                        "profile_picture_url": u.get("profile_picture_url")
                    })
            return results
            
        try:
            res = supabase_client.from_("users").select("id, name, email, username, profile_picture_url").or_(f"name.ilike.%{query}%,username.ilike.%{query}%,email.ilike.%{query}%").limit(10).execute()
            results = []
            if res and res.data:
                for u in res.data:
                    results.append({
                        "id": str(u["id"]),
                        "name": u.get("name") or "User",
                        "username": u.get("username") or "",
                        "email": u.get("email") or "",
                        "profile_picture_url": u.get("profile_picture_url")
                    })
            return results
        except Exception:
            return []

db_repository = DBRepository()
