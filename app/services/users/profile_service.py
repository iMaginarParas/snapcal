from typing import Dict, Any, List, Optional
from app.repositories.db_repository import db_repository
from app.schemas.users import ProfileUpdateRequest
from app.services.profile.calculation_engine import CalculationEngine
from datetime import datetime

class ProfileService:
    def get_profile(self, user_id: str) -> dict:
        """Fetches the calculated profile. If missing, initializes it with defaults."""
        profile = db_repository.get_calculated_profile(user_id)
        core_user = db_repository.get_user_profile(user_id) or {}
        
        if not profile:
            # If the calculated profile table row is missing, initialize it
            age = core_user.get("age") or 25
            gender = "Male"
            height = float(core_user.get("height") or 175.0)
            weight = float(core_user.get("weight") or 75.0)
            goal = core_user.get("goals") or "Build Muscle"
            activity = "Moderately Active"
            
            # Recalculate everything
            bmi, bmi_cat = CalculationEngine.calculate_bmi(weight, height)
            bmr = CalculationEngine.calculate_bmr(weight, height, age, gender)
            tdee = CalculationEngine.calculate_tdee(bmr, activity)
            calories = CalculationEngine.calculate_target_calories(tdee, goal)
            macros = CalculationEngine.calculate_macros(calories, weight, goal)
            water = CalculationEngine.calculate_water(weight, activity)
            
            profile_data = {
                "age": age,
                "gender": gender,
                "height_cm": height,
                "current_weight": weight,
                "target_weight": weight,
                "activity_level": activity,
                "goal": goal,
                "bmi": bmi,
                "bmi_category": bmi_cat,
                "bmr": bmr,
                "tdee": tdee,
                "target_calories": calories,
                "protein_target": macros["protein"],
                "carb_target": macros["carbs"],
                "fat_target": macros["fat"],
                "fiber_target": macros["fiber"],
                "water_target": water
            }
            profile = db_repository.upsert_calculated_profile(user_id, profile_data)
            
            # Also log initial weight to history
            db_repository.add_weight_history_entry(user_id, weight, bmi)
            
        # Merge names and username from core user table for completeness
        result = dict(profile)
        result["name"] = core_user.get("name") or "Guest User"
        result["username"] = core_user.get("username") or user_id
        result["profile_picture_url"] = core_user.get("profile_picture_url")
        
        return {"success": True, "data": result}

    def update_profile(self, user_id: str, payload: ProfileUpdateRequest) -> dict:
        """Recalculates profile metrics and updates profiles & users tables."""
        # 1. Update core table fields (name, username) if provided
        core_updates = {}
        if payload.name is not None:
            core_updates["name"] = payload.name
        if payload.username is not None:
            core_updates["username"] = payload.username
        if payload.goals is not None:
            core_updates["goals"] = payload.goals
            
        # Also write weight/height compatibility fields to users table
        if payload.weight is not None:
            core_updates["weight"] = payload.weight
        if payload.height is not None:
            core_updates["height"] = payload.height
            
        if core_updates:
            db_repository.update_user_profile(user_id, core_updates)

        # 2. Get existing calculations profile
        profile = db_repository.get_calculated_profile(user_id) or {}
        
        # 3. Merge new fields
        age = payload.age if payload.age is not None else (profile.get("age") or 25)
        gender = payload.gender if payload.gender is not None else (profile.get("gender") or "Male")
        height = payload.height if payload.height is not None else (profile.get("height_cm") or 175.0)
        weight = payload.weight if payload.weight is not None else (profile.get("current_weight") or 75.0)
        target_weight = payload.target_weight if payload.target_weight is not None else (profile.get("target_weight") or weight)
        activity = payload.activity_level if payload.activity_level is not None else (profile.get("activity_level") or "Moderately Active")
        goal = payload.goal if payload.goal is not None else (payload.goals if payload.goals is not None else (profile.get("goal") or "Build Muscle"))

        # 4. Perform calculations on backend
        bmi, bmi_cat = CalculationEngine.calculate_bmi(weight, height)
        bmr = CalculationEngine.calculate_bmr(weight, height, age, gender)
        tdee = CalculationEngine.calculate_tdee(bmr, activity)
        calories = CalculationEngine.calculate_target_calories(tdee, goal)
        macros = CalculationEngine.calculate_macros(calories, weight, goal)
        water = CalculationEngine.calculate_water(weight, activity)

        # 5. Handle weight history logging
        prev_weight = profile.get("current_weight")
        if prev_weight is None or abs(prev_weight - weight) > 0.01:
            db_repository.add_weight_history_entry(user_id, weight, bmi)

        # 6. Upsert calculated profile table
        profile_data = {
            "age": age,
            "gender": gender,
            "height_cm": height,
            "current_weight": weight,
            "target_weight": target_weight,
            "activity_level": activity,
            "goal": goal,
            "bmi": bmi,
            "bmi_category": bmi_cat,
            "bmr": bmr,
            "tdee": tdee,
            "target_calories": calories,
            "protein_target": macros["protein"],
            "carb_target": macros["carbs"],
            "fat_target": macros["fat"],
            "fiber_target": macros["fiber"],
            "water_target": water,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        updated_profile = db_repository.upsert_calculated_profile(user_id, profile_data)
        
        # 7. Construct and return final merged dictionary
        result = dict(updated_profile)
        core_user = db_repository.get_user_profile(user_id) or {}
        result["name"] = core_user.get("name") or "Guest User"
        result["username"] = core_user.get("username") or user_id
        result["profile_picture_url"] = core_user.get("profile_picture_url")

        return {"success": True, "data": result}

    def get_weight_history(self, user_id: str) -> dict:
        """Fetches historical weight logs and computes trends."""
        records = db_repository.get_weight_history_records(user_id) or []
        
        weight_change = 0.0
        goal_progress = 0.0
        
        if records:
            # Sort records chronologically
            records = sorted(records, key=lambda x: x.get("recorded_at", ""))
            
            first_weight = float(records[0].get("weight") or 0.0)
            last_weight = float(records[-1].get("weight") or 0.0)
            weight_change = last_weight - first_weight
            
            # Progress calculation if target weight is set
            profile = db_repository.get_calculated_profile(user_id)
            if profile and profile.get("target_weight"):
                target = float(profile["target_weight"])
                total_to_lose = first_weight - target
                if abs(total_to_lose) > 0.1:
                    lost_so_far = first_weight - last_weight
                    goal_progress = (lost_so_far / total_to_lose) * 100.0
                    goal_progress = max(0.0, min(100.0, goal_progress)) # clamp between 0 and 100
                    
        return {
            "success": True,
            "data": {
                "history": records,
                "weight_change": round(weight_change, 1),
                "goal_progress": round(goal_progress, 1)
            }
        }

profile_service = ProfileService()
