from typing import Dict, Any, List, Optional
from app.database.supabase import supabase_client
from datetime import datetime

class DBRepository:
    """Centralized database repository handling all Supabase queries."""
    def __init__(self):
        self._in_memory_dms = []

    # --- Users & Profiles ---
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        res = supabase_client.from_("users").select("*").eq("id", user_id).single().execute()
        return res.data if res else None

    def create_user_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("users").insert(profile).execute()
        return res.data[0] if res and res.data else {}

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("users").update(updates).eq("id", user_id).execute()
        return res.data[0] if res and res.data else {}

    def check_username_exists(self, username: str, exclude_user_id: str) -> bool:
        res = supabase_client.from_("users").select("id").eq("username", username).neq("id", exclude_user_id).execute()
        return bool(res.data)

    def get_calculated_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        res = supabase_client.from_("profiles").select("*").eq("user_id", user_id).maybe_single().execute()
        return res.data if res else None

    def upsert_calculated_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        profile_data["user_id"] = user_id
        res = supabase_client.from_("profiles").upsert(profile_data).execute()
        return res.data[0] if res and res.data else {}

    def add_weight_history_entry(self, user_id: str, weight: float, bmi: float) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "weight": weight,
            "bmi": bmi
        }
        res = supabase_client.from_("weight_history").insert(payload).execute()
        return res.data[0] if res and res.data else {}

    def get_weight_history_records(self, user_id: str) -> List[Dict[str, Any]]:
        res = supabase_client.from_("weight_history").select("*").eq("user_id", user_id).order("recorded_at", desc=False).execute()
        return res.data if res else []

    # --- Workouts ---
    def get_workouts(self, user_id: str, date: Optional[str] = None, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        query = supabase_client.from_("workouts").select("*").eq("user_id", user_id)
        if date:
            query = query.gte("completed_at", f"{date}T00:00:00.000Z").lte("completed_at", f"{date}T23:59:59.999Z")
        res = query.order("completed_at", desc=True).range(offset, offset + limit - 1).execute()
        return res.data if res else []

    def create_workout(self, user_id: str, workout_data: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("workouts").insert(workout_data).execute()
        return res.data[0] if res and res.data else {}

    def delete_workout(self, user_id: str, workout_id: str) -> bool:
        res = supabase_client.from_("workouts").delete().eq("id", workout_id).eq("user_id", user_id).execute()
        return bool(res.data) if res else False

    # --- Daily Stats ---
    def get_daily_stats(self, user_id: str, date_str: str) -> Optional[Dict[str, Any]]:
        res = supabase_client.from_("daily_stats").select("*").eq("user_id", user_id).eq("date", date_str).maybe_single().execute()
        return res.data if res else None

    def create_daily_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("daily_stats").insert(stats).execute()
        return res.data[0] if res and res.data else {}

    def update_daily_stats(self, user_id: str, date_str: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("daily_stats").update(updates).eq("user_id", user_id).eq("date", date_str).execute()
        return res.data[0] if res and res.data else {}

    # --- Measurements ---
    def get_measurements(self, user_id: str, metric_type: Optional[str] = None) -> List[Dict[str, Any]]:
        query = supabase_client.from_("measurement_logs").select("*").eq("user_id", user_id)
        if metric_type:
            query = query.eq("metric_type", metric_type)
        res = query.order("logged_at", desc=True).execute()
        return res.data

    def log_measurement(self, user_id: str, measurement: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("measurement_logs").insert(measurement).execute()
        return res.data[0] if res and res.data else {}

    def delete_measurement(self, user_id: str, measurement_id: str) -> bool:
        res = supabase_client.from_("measurement_logs").delete().eq("id", measurement_id).eq("user_id", user_id).execute()
        return bool(res.data) if res else False

    # --- Fasting Logs ---
    def get_active_fast(self, user_id: str) -> Optional[Dict[str, Any]]:
        res = supabase_client.from_("fasting_logs").select("*").eq("user_id", user_id).eq("completed", False).maybe_single().execute()
        return res.data if res else None

    def start_fast(self, user_id: str, protocol: str) -> Dict[str, Any]:
        db_payload = {
            "user_id": user_id,
            "protocol": protocol,
            "start_time": datetime.utcnow().isoformat() + "Z",
            "completed": False
        }
        res = supabase_client.from_("fasting_logs").insert(db_payload).execute()
        return res.data[0] if res and res.data else {}

    def stop_fast(self, user_id: str, fast_id: str) -> Optional[Dict[str, Any]]:
        db_payload = {
            "completed": True,
            "end_time": datetime.utcnow().isoformat() + "Z"
        }
        res = supabase_client.from_("fasting_logs").update(db_payload).eq("id", fast_id).eq("user_id", user_id).execute()
        return res.data[0] if res and res.data else None

    # --- Meals & Food ---
    def get_meals(self, user_id: str, date_str: str) -> List[Dict[str, Any]]:
        res = supabase_client.from_("meals").select("*, food_items(*)").eq("user_id", user_id).gte("logged_at", f"{date_str}T00:00:00.000Z").lte("logged_at", f"{date_str}T23:59:59.999Z").execute()
        return res.data if res else []

    def create_meal(self, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("meals").insert(meal_data).execute()
        return res.data[0] if res and res.data else {}

    def create_food_items(self, food_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        res = supabase_client.from_("food_items").insert(food_items).execute()
        return res.data

    # --- Groups & Challenges ---
    def get_groups(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = supabase_client.from_("groups").select("*").execute()
            groups = res.data if res else []
        except Exception:
            groups = []

        for g in groups:
            gid = str(g.get("id"))
            try:
                members_res = supabase_client.from_("group_members").select("user_id, users(name, profile_picture_url)").eq("group_id", gid).execute()
                members = members_res.data if members_res and members_res.data else []
            except Exception:
                try:
                    members_res = supabase_client.from_("group_members").select("user_id").eq("group_id", gid).execute()
                    members = members_res.data if members_res and members_res.data else []
                except Exception:
                    members = []
            
            is_joined = any(str(m.get("user_id")) == str(user_id) for m in members)
            g["isJoined"] = is_joined
            g["memberCount"] = max(len(members), 1)
            avatars = []
            for m in members[:3]:
                u = m.get("users") or {}
                if isinstance(u, dict) and u.get("profile_picture_url"):
                    avatars.append(u["profile_picture_url"])
            g["avatars"] = avatars
        return groups

    def create_group(self, group_data: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("groups").insert(group_data).execute()
        group = res.data[0] if res and res.data else {}
        if group and "id" in group and "created_by" in group and group["created_by"]:
            try:
                supabase_client.from_("group_members").insert({
                    "group_id": group["id"],
                    "user_id": group["created_by"],
                    "joined_at": datetime.utcnow().isoformat() + "Z"
                }).execute()
            except Exception:
                pass
        return group

    def join_group(self, user_id: str, group_id: str) -> bool:
        try:
            existing = supabase_client.from_("group_members").select("id").eq("group_id", group_id).eq("user_id", user_id).maybe_single().execute()
            if existing and existing.data:
                return True
            payload = {
                "group_id": group_id,
                "user_id": user_id,
                "joined_at": datetime.utcnow().isoformat() + "Z"
            }
            supabase_client.from_("group_members").insert(payload).execute()
            return True
        except Exception:
            return True

    def leave_group(self, user_id: str, group_id: str) -> bool:
        try:
            supabase_client.from_("group_members").delete().eq("group_id", group_id).eq("user_id", user_id).execute()
        except Exception:
            pass
        return True

    def get_group_messages(self, group_id: str) -> List[Dict[str, Any]]:
        try:
            res = supabase_client.from_("group_messages").select("id, group_id, user_id, message, created_at, users(name, profile_picture_url)").eq("group_id", group_id).order("created_at", desc=False).execute()
            data = res.data if res and res.data else []
        except Exception:
            try:
                res = supabase_client.from_("group_messages").select("*").eq("group_id", group_id).order("created_at", desc=False).execute()
                data = res.data if res and res.data else []
            except Exception:
                data = []

        messages = []
        for m in data:
            u = m.get("users") or {}
            sender_name = u.get("name") if isinstance(u, dict) else "Member"
            sender_avatar = u.get("profile_picture_url") if isinstance(u, dict) else None
            messages.append({
                "id": str(m.get("id")),
                "group_id": str(m.get("group_id")),
                "user_id": str(m.get("user_id")),
                "sender_name": sender_name or "Member",
                "sender_avatar": sender_avatar,
                "message": m.get("message") or "",
                "created_at": m.get("created_at")
            })
        return messages

    def send_group_message(self, user_id: str, group_id: str, message: str) -> Dict[str, Any]:
        payload = {
            "group_id": group_id,
            "user_id": user_id,
            "message": message,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        try:
            res = supabase_client.from_("group_messages").insert(payload).execute()
            return res.data[0] if res and res.data else payload
        except Exception:
            return payload

    def get_challenges(self) -> List[Dict[str, Any]]:
        res = supabase_client.from_("challenges").select("*").execute()
        return res.data if res else []

    def get_user_challenge(self, user_id: str, challenge_id: str) -> Optional[Dict[str, Any]]:
        res = supabase_client.from_("user_challenges").select("*").eq("user_id", user_id).eq("challenge_id", challenge_id).maybe_single().execute()
        return res.data if res else None

    def create_user_challenge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("user_challenges").insert(data).execute()
        return res.data[0] if res and res.data else {}

    def update_user_challenge(self, challenge_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("user_challenges").update(updates).eq("id", challenge_id).execute()
        return res.data[0] if res and res.data else {}

    # --- Supplements ---
    def get_supplements(self, user_id: str) -> List[Dict[str, Any]]:
        res = supabase_client.from_("supplements").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
        return res.data if res else []

    def add_supplement(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        data["user_id"] = user_id
        res = supabase_client.from_("supplements").insert(data).execute()
        return res.data[0] if res and res.data else {}

    def delete_supplement(self, user_id: str, supplement_id: str) -> bool:
        res = supabase_client.from_("supplements").delete().eq("id", supplement_id).eq("user_id", user_id).execute()
        return bool(res.data) if res else False

    # --- Referrals ---
    def get_referral_info(self, user_id: str) -> Dict[str, Any]:
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

    # --- Friends Helpers ---
    @staticmethod
    def _resolve_display_name(name: Optional[str] = None, username: Optional[str] = None, email: Optional[str] = None) -> str:
        n = (name or "").strip()
        u = (username or "").strip()
        e = (email or "").strip()
        
        if n and n.lower() not in ["user", "friend user", "user user", "none", "null"]:
            return n
        if u and u.lower() not in ["user", "none", "null"]:
            return u
        if e and "@" in e:
            prefix = e.split("@")[0]
            if prefix and prefix.lower() not in ["user", "none", "null"]:
                return prefix
        return n or u or "User"

    @staticmethod
    def _get_avatar_initials(display_name: str) -> str:
        cleaned = (display_name or "").strip()
        if not cleaned:
            return "U"
        parts = [p for p in cleaned.split(" ") if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return cleaned[:2].upper()

    # --- Friends ---
    def get_friends(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = supabase_client.from_("friendships").select("id, status, friend_id, users!friend_id(id, name, email, username, profile_picture_url)").eq("user_id", user_id).eq("status", "accepted").execute()
            data = res.data
        except Exception:
            try:
                res = supabase_client.from_("friendships").select("id, status, friend_id").eq("user_id", user_id).eq("status", "accepted").execute()
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

                disp_name = self._resolve_display_name(
                    friend_user.get("name"), 
                    friend_user.get("username"), 
                    friend_user.get("email")
                )
                avatar_inits = self._get_avatar_initials(disp_name)
                    
                result.append({
                    "id": str(f.get("id")),
                    "friend_id": str(fid),
                    "name": disp_name,
                    "username": friend_user.get("username") or "",
                    "email": friend_user.get("email") or "",
                    "profile_picture_url": friend_user.get("profile_picture_url"),
                    "steps": steps,
                    "calories": int(steps * 0.045),
                    "avatar": avatar_inits,
                    "status": "Active"
                })
        return result

    def get_friend_suggestions(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            friend_ids = set()
            try:
                friends_res = supabase_client.from_("friendships").select("friend_id").eq("user_id", user_id).execute()
                if friends_res and friends_res.data:
                    friend_ids = {str(f["friend_id"]) for f in friends_res.data}
            except Exception:
                pass
            friend_ids.add(str(user_id))
            
            users_res = supabase_client.from_("users").select("id, name, email, username, profile_picture_url").limit(50).execute()
            suggestions = []
            if users_res and users_res.data:
                for u in users_res.data:
                    uid_str = str(u["id"])
                    if uid_str not in friend_ids:
                        disp_name = self._resolve_display_name(u.get("name"), u.get("username"), u.get("email"))
                        suggestions.append({
                            "id": uid_str,
                            "name": disp_name,
                            "username": u.get("username") or "",
                            "email": u.get("email") or "",
                            "profile_picture_url": u.get("profile_picture_url")
                        })
            return suggestions[:5]
        except Exception:
            return []

    def add_friend(self, user_id: str, identifier: str) -> Dict[str, Any]:
        clean_id = identifier.strip()
        if not clean_id:
            raise ValueError("Invalid user search input")

        friend_user = None
        # Try PostgREST query first
        try:
            user_res = supabase_client.from_("users").select("id, email, name, username").or_(f"email.ilike.{clean_id},username.ilike.{clean_id},name.ilike.{clean_id}").execute()
            if user_res and user_res.data:
                friend_user = user_res.data[0]
        except Exception:
            pass

        # Fallback query: scan users
        if not friend_user:
            try:
                all_users = supabase_client.from_("users").select("id, email, name, username").limit(100).execute()
                if all_users and all_users.data:
                    q_lower = clean_id.lower()
                    for u in all_users.data:
                        u_email = (u.get("email") or "").lower()
                        u_uname = (u.get("username") or "").lower()
                        u_name = (u.get("name") or "").lower()
                        if q_lower in u_email or q_lower in u_uname or q_lower in u_name or u_email == q_lower or u_uname == q_lower:
                            friend_user = u
                            break
            except Exception:
                pass
        
        if not friend_user:
            raise ValueError("User not found")
            
        friend_id = friend_user["id"]
        if str(friend_id) == str(user_id):
            raise ValueError("Cannot add yourself as a friend")
            
        try:
            existing = supabase_client.from_("friendships").select("id, status").eq("user_id", user_id).eq("friend_id", friend_id).maybe_single().execute()
            if existing and existing.data:
                st = existing.data.get("status")
                if st == "accepted":
                    raise ValueError("You are already friends with this user")
                elif st == "pending":
                    raise ValueError("Friend request already sent")
                
            req_data = {"user_id": user_id, "friend_id": friend_id, "status": "pending"}
            supabase_client.from_("friendships").upsert([req_data]).execute()
            return {"user_id": user_id, "friend_id": friend_id, "status": "pending", "message": "Friend request sent"}
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to send friend request: {e}")

    def get_pending_friend_requests(self, user_id: str) -> List[Dict[str, Any]]:
        """Returns incoming pending friend requests for the user."""
        try:
            res = supabase_client.from_("friendships").select("id, created_at, user_id, users!user_id(id, name, email, username, profile_picture_url)").eq("friend_id", user_id).eq("status", "pending").execute()
            data = res.data or []
        except Exception:
            try:
                res = supabase_client.from_("friendships").select("id, created_at, user_id").eq("friend_id", user_id).eq("status", "pending").execute()
                data = res.data or []
                for item in data:
                    sender_id = item["user_id"]
                    user_res = supabase_client.from_("users").select("id, name, email, username, profile_picture_url").eq("id", sender_id).single().execute()
                    item["users"] = user_res.data if user_res else {}
            except Exception:
                data = []

        requests = []
        for req in data:
            sender = req.get("users") or {}
            sender_id = req.get("user_id") or sender.get("id")
            if not sender_id:
                continue
            disp_name = self._resolve_display_name(sender.get("name"), sender.get("username"), sender.get("email"))
            requests.append({
                "id": str(req.get("id")),
                "sender_id": str(sender_id),
                "name": disp_name,
                "email": sender.get("email") or "",
                "username": sender.get("username") or "",
                "profile_picture_url": sender.get("profile_picture_url"),
                "avatar": self._get_avatar_initials(disp_name),
                "created_at": req.get("created_at")
            })
        return requests

    def accept_friend_request(self, user_id: str, request_id: str) -> Dict[str, Any]:
        """Accepts a pending friend request and creates mutual accepted friendship."""
        try:
            req_res = supabase_client.from_("friendships").select("id, user_id, friend_id").eq("id", request_id).eq("friend_id", user_id).single().execute()
            if not req_res or not req_res.data:
                raise ValueError("Friend request not found or unauthorized")
            
            sender_id = req_res.data["user_id"]
            
            # Update incoming request to accepted
            supabase_client.from_("friendships").update({"status": "accepted"}).eq("id", request_id).execute()
            
            # Upsert reciprocal friendship row (user_id -> sender_id)
            reciprocal = {"user_id": user_id, "friend_id": sender_id, "status": "accepted"}
            supabase_client.from_("friendships").upsert([reciprocal]).execute()
            
            return {"success": True, "message": "Friend request accepted"}
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to accept friend request: {e}")

    def decline_friend_request(self, user_id: str, request_id: str) -> Dict[str, Any]:
        """Declines / deletes a pending friend request."""
        try:
            supabase_client.from_("friendships").delete().eq("id", request_id).eq("friend_id", user_id).execute()
            return {"success": True, "message": "Friend request declined"}
        except Exception as e:
            raise ValueError(f"Failed to decline friend request: {e}")

    def search_users(self, query: str) -> List[Dict[str, Any]]:
        clean_q = query.strip()
        if not clean_q:
            return []

        # 1. Try PostgREST wildcard query
        try:
            res = supabase_client.from_("users").select("id, name, email, username, profile_picture_url").or_(f"name.ilike.*{clean_q}*,username.ilike.*{clean_q}*,email.ilike.*{clean_q}*").limit(10).execute()
            if res and res.data:
                results = []
                for u in res.data:
                    results.append({
                        "id": str(u["id"]),
                        "name": self._resolve_display_name(u.get("name"), u.get("username"), u.get("email")),
                        "username": u.get("username") or "",
                        "email": u.get("email") or "",
                        "profile_picture_url": u.get("profile_picture_url")
                    })
                return results
        except Exception:
            pass

        # 2. Robust fallback filter across public.users
        try:
            res = supabase_client.from_("users").select("id, name, email, username, profile_picture_url").limit(100).execute()
            results = []
            if res and res.data:
                q_lower = clean_q.lower()
                for u in res.data:
                    name = (u.get("name") or "").lower()
                    username = (u.get("username") or "").lower()
                    email = (u.get("email") or "").lower()
                    if q_lower in name or q_lower in username or q_lower in email:
                        results.append({
                            "id": str(u["id"]),
                            "name": self._resolve_display_name(u.get("name"), u.get("username"), u.get("email")),
                            "username": u.get("username") or "",
                            "email": u.get("email") or "",
                            "profile_picture_url": u.get("profile_picture_url")
                        })
            return results[:10]
        except Exception:
            return []

    def create_support_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("support_tickets").insert(ticket_data).execute()
        return res.data[0] if res and res.data else {}

    # --- Challenges Additions ---
    def get_user_challenges(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = supabase_client.from_("user_challenges").select("*, challenges(*)").eq("user_id", user_id).execute()
            return res.data if res and res.data else []
        except Exception:
            try:
                res = supabase_client.from_("user_challenges").select("*").eq("user_id", user_id).execute()
                return res.data if res and res.data else []
            except Exception:
                return []

    def join_challenge(self, user_id: str, challenge_id: str) -> Dict[str, Any]:
        existing = self.get_user_challenge(user_id, challenge_id)
        if existing:
            return existing
        ins_payload = {
            "user_id": user_id,
            "challenge_id": challenge_id,
            "progress": 0,
            "completed": False,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        return self.create_user_challenge(ins_payload)

    # --- Leaderboard ---
    def get_leaderboard(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            users_res = supabase_client.from_("users").select("id, name, profile_picture_url").limit(50).execute()
            users = users_res.data if users_res and users_res.data else []
            
            leaderboard = []
            for u in users:
                uid = str(u["id"])
                w_res = supabase_client.from_("workouts").select("id").eq("user_id", uid).execute()
                w_count = len(w_res.data) if w_res and w_res.data else 0
                
                s_res = supabase_client.from_("daily_stats").select("steps").eq("user_id", uid).execute()
                total_steps = sum([s.get("steps") or 0 for s in s_res.data]) if s_res and s_res.data else 0
                
                pts = (w_count * 100) + (total_steps // 100)
                name = u.get("name") or "User"
                avatar = "".join([e[0] for e in name.split(" ") if e]).upper()[:2] or "US"
                
                leaderboard.append({
                    "id": uid,
                    "name": name,
                    "avatar": avatar,
                    "points": pts,
                    "isMe": uid == str(user_id)
                })
            
            leaderboard.sort(key=lambda x: x["points"], reverse=True)
            return leaderboard
        except Exception:
            return []

    # --- Badges ---
    def get_user_badges(self, user_id: str) -> List[str]:
        try:
            res = supabase_client.from_("user_badges").select("badge_id").eq("user_id", user_id).execute()
            if res and res.data:
                return [b["badge_id"] for b in res.data if "badge_id" in b]
            return []
        except Exception:
            return []

    def award_badge(self, user_id: str, badge_id: str) -> Dict[str, Any]:
        try:
            existing = supabase_client.from_("user_badges").select("id").eq("user_id", user_id).eq("badge_id", badge_id).maybe_single().execute()
            if existing and existing.data:
                return existing.data
            payload = {
                "user_id": user_id,
                "badge_id": badge_id,
                "earned_at": datetime.utcnow().isoformat() + "Z"
            }
            res = supabase_client.from_("user_badges").insert(payload).execute()
            return res.data[0] if res and res.data else payload
        except Exception:
            return {"user_id": user_id, "badge_id": badge_id}

    # --- Nutrition Goals ---
    def get_nutrition_goals(self, user_id: str) -> Dict[str, Any]:
        try:
            res = supabase_client.from_("users").select("calorie_goal, protein_goal, carbs_goal, fats_goal").eq("id", user_id).maybe_single().execute()
            if res and res.data:
                return {
                    "calorie_goal": res.data.get("calorie_goal") or 2000,
                    "protein_goal": res.data.get("protein_goal") or 130,
                    "carbs_goal": res.data.get("carbs_goal") or 220,
                    "fats_goal": res.data.get("fats_goal") or 65,
                }
        except Exception:
            pass
        return {"calorie_goal": 2000, "protein_goal": 130, "carbs_goal": 220, "fats_goal": 65}

    def update_nutrition_goals(self, user_id: str, goals: Dict[str, Any]) -> Dict[str, Any]:
        try:
            res = supabase_client.from_("users").update(goals).eq("id", user_id).execute()
            return res.data[0] if res and res.data else goals
        except Exception:
            return goals

    # --- Supplement Logs ---
    def log_supplement_taken(self, user_id: str, supplement_id: str, date: str) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "supplement_id": supplement_id,
            "date": date,
            "taken_at": datetime.utcnow().isoformat() + "Z"
        }
        try:
            res = supabase_client.from_("supplement_logs").insert(payload).execute()
            return res.data[0] if res and res.data else payload
        except Exception:
            return payload

    def get_supplement_logs(self, user_id: str, date: str) -> List[Dict[str, Any]]:
        try:
            res = supabase_client.from_("supplement_logs").select("*").eq("user_id", user_id).eq("date", date).execute()
            return res.data if res and res.data else []
        except Exception:
            return []

    # --- Group Invites ---
    def invite_to_group(self, group_id: str, inviter_id: str, invitee_id: str) -> Dict[str, Any]:
        payload = {
            "group_id": group_id,
            "inviter_id": inviter_id,
            "invitee_id": invitee_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        try:
            res = supabase_client.from_("group_invites").insert(payload).execute()
            return res.data[0] if res and res.data else payload
        except Exception:
            return payload

    def get_group_invites(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = supabase_client.from_("group_invites").select("*, groups(*), users!inviter_id(name)").eq("invitee_id", user_id).eq("status", "pending").execute()
            return res.data if res and res.data else []
        except Exception:
            return []

    def accept_group_invite(self, user_id: str, group_id: str) -> bool:
        try:
            supabase_client.from_("group_invites").update({"status": "accepted"}).eq("invitee_id", user_id).eq("group_id", group_id).execute()
            self.join_group(user_id, group_id)
            return True
        except Exception:
            self.join_group(user_id, group_id)
            return True

    # --- Direct Messages ---
    def get_dm_messages(self, user_id: str, friend_id: str) -> List[Dict[str, Any]]:
        """Fetch all DM messages between two users (bidirectional)."""
        uid_str = str(user_id)
        fid_str = str(friend_id)
        db_msgs = []
        try:
            res1 = supabase_client.from_("direct_messages").select("*").eq("sender_id", uid_str).eq("receiver_id", fid_str).execute()
            res2 = supabase_client.from_("direct_messages").select("*").eq("sender_id", fid_str).eq("receiver_id", uid_str).execute()
            msgs1 = res1.data if res1 and res1.data else []
            msgs2 = res2.data if res2 and res2.data else []
            db_msgs = msgs1 + msgs2
        except Exception:
            pass

        # Combine with in-memory DMs
        mem_msgs = [
            m for m in getattr(self, "_in_memory_dms", [])
            if (str(m.get("sender_id")) == uid_str and str(m.get("receiver_id")) == fid_str) or
               (str(m.get("sender_id")) == fid_str and str(m.get("receiver_id")) == uid_str)
        ]

        seen_ids = set()
        combined = []
        for m in db_msgs + mem_msgs:
            mid = m.get("id")
            if mid and mid in seen_ids:
                continue
            if mid:
                seen_ids.add(mid)
            combined.append(m)

        combined.sort(key=lambda m: m.get("created_at", ""))
        return combined

    def send_dm(self, sender_id: str, receiver_id: str, message: str) -> Dict[str, Any]:
        """Save a direct message to the database."""
        payload = {
            "id": f"dm_{int(datetime.utcnow().timestamp() * 1000)}",
            "sender_id": str(sender_id),
            "receiver_id": str(receiver_id),
            "message": message,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "read": False,
        }
        if not hasattr(self, "_in_memory_dms"):
            self._in_memory_dms = []
        self._in_memory_dms.append(payload)

        try:
            res = supabase_client.from_("direct_messages").insert(payload).execute()
            if res and res.data:
                return res.data[0]
        except Exception:
            pass
        return payload

    # --- Challenge Invites ---
    def invite_friend_to_challenge(self, inviter_id: str, friend_id: str) -> Dict[str, Any]:
        """Send a challenge invite notification between friends."""
        payload = {
            "inviter_id": inviter_id,
            "invitee_id": friend_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        try:
            res = supabase_client.from_("challenge_invites").insert(payload).execute()
            return res.data[0] if res and res.data else payload
        except Exception:
            return payload

db_repository = DBRepository()

