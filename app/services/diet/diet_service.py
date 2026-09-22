import math
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.repositories.diet_plan_repository import diet_plan_repository
from app.repositories.nutrition_repository import NutritionRepository
from app.schemas.diet_plans import (
    DietPlanCreate,
    SendDailyDietPlanRequest,
    CoachMealFeedbackRequest,
    AIDietPlanGenerateRequest
)

nutrition_repo = NutritionRepository()

class DietService:
    def list_plans(self, coach_id: Optional[str] = None, client_id: Optional[str] = None, is_template: Optional[bool] = None) -> List[Dict[str, Any]]:
        return diet_plan_repository.get_plans(coach_id=coach_id, client_id=client_id, is_template=is_template)

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        return diet_plan_repository.get_plan_by_id(plan_id)

    def create_plan(self, payload: DietPlanCreate) -> Dict[str, Any]:
        data = payload.dict()
        # Compute summary if not provided
        self._recalculate_totals_if_needed(data)
        return diet_plan_repository.create_plan(data)

    def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        self._recalculate_totals_if_needed(updates)
        return diet_plan_repository.update_plan(plan_id, updates)

    def delete_plan(self, plan_id: str) -> bool:
        return diet_plan_repository.delete_plan(plan_id)

    def send_daily_diet_plan(self, payload: SendDailyDietPlanRequest) -> Dict[str, Any]:
        data = payload.dict()
        self._recalculate_totals_if_needed(data)
        dispatch = diet_plan_repository.send_daily_diet_plan(data)
        return {
            "success": True,
            "message": f"Daily diet plan successfully dispatched to client {payload.client_id} for {payload.target_date}",
            "data": dispatch
        }

    def get_client_today_plan(self, client_id: str, date_str: Optional[str] = None) -> Dict[str, Any]:
        today_date = date_str or datetime.utcnow().strftime("%Y-%m-%d")
        plan = diet_plan_repository.get_client_today_plan(client_id, today_date)
        feedbacks = diet_plan_repository.get_feedback_for_client(client_id, today_date)
        return {
            "success": True,
            "date": today_date,
            "has_plan": plan is not None,
            "plan": plan,
            "coach_feedbacks": feedbacks
        }

    def get_client_diet_telemetry(self, client_id: str, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates full nutritional adherence comparing prescribed daily diet plan
        against actual meals logged by client in SabTrack.
        """
        today_date = date_str or datetime.utcnow().strftime("%Y-%m-%d")
        
        # 1. Prescribed plan
        prescribed_plan = diet_plan_repository.get_client_today_plan(client_id, today_date) or {}
        target_calories = int(prescribed_plan.get("total_calories") or 2000)
        target_protein = float(prescribed_plan.get("protein_g") or 140.0)
        target_carbs = float(prescribed_plan.get("carbs_g") or 200.0)
        target_fats = float(prescribed_plan.get("fats_g") or 65.0)
        target_water = float(prescribed_plan.get("water_liters") or 3.0)

        # 2. Actual logged meals from SabTrack
        actual_summary = nutrition_repo.get_daily_summary(client_id, today_date)
        actual_calories = int(actual_summary.get("calories") or 0)
        actual_protein = float(actual_summary.get("protein") or 0.0)
        actual_carbs = float(actual_summary.get("carbs") or 0.0)
        actual_fats = float(actual_summary.get("fat") or 0.0)
        actual_meals = actual_summary.get("meals") or []

        # 3. Adherence Score Calculation (weighted: calories 40%, protein 35%, carbs/fat 25%)
        cal_score = max(0.0, 100.0 - abs(actual_calories - target_calories) / max(target_calories, 1) * 100.0) if actual_calories > 0 else 0.0
        prot_score = min(100.0, (actual_protein / max(target_protein, 1.0)) * 100.0) if actual_protein > 0 else 0.0
        macro_balance = max(0.0, 100.0 - (abs(actual_carbs - target_carbs) + abs(actual_fats - target_fats)) / max(target_carbs + target_fats, 1.0) * 50.0) if (actual_carbs + actual_fats) > 0 else 0.0
        
        adherence_percentage = round((cal_score * 0.4) + (prot_score * 0.35) + (macro_balance * 0.25), 1)
        if actual_calories == 0:
            status = "No Meals Logged Yet"
        elif adherence_percentage >= 85:
            status = "Optimal Adherence"
        elif adherence_percentage >= 70:
            status = "On Track"
        elif actual_calories > target_calories + 250:
            status = "Over Calorie Target"
        elif actual_protein < target_protein * 0.75:
            status = "Protein Under Target"
        else:
            status = "Moderate Adherence"

        # 4. Feedbacks
        feedbacks = diet_plan_repository.get_feedback_for_client(client_id, today_date)

        return {
            "client_id": client_id,
            "date": today_date,
            "status": status,
            "adherence_percentage": adherence_percentage,
            "prescribed": {
                "title": prescribed_plan.get("title") or "Standard Target",
                "calories": target_calories,
                "protein": target_protein,
                "carbs": target_carbs,
                "fats": target_fats,
                "water_liters": target_water,
                "meals": prescribed_plan.get("meals") or []
            },
            "actual": {
                "calories": actual_calories,
                "protein": round(actual_protein, 1),
                "carbs": round(actual_carbs, 1),
                "fats": round(actual_fats, 1),
                "meal_count": len(actual_meals),
                "meals": actual_meals
            },
            "deltas": {
                "calories": actual_calories - target_calories,
                "protein": round(actual_protein - target_protein, 1),
                "carbs": round(actual_carbs - target_carbs, 1),
                "fats": round(actual_fats - target_fats, 1)
            },
            "feedbacks": feedbacks
        }

    def save_coach_feedback(self, payload: CoachMealFeedbackRequest) -> Dict[str, Any]:
        return diet_plan_repository.save_coach_feedback(payload.dict())

    def generate_ai_diet_plan(self, payload: AIDietPlanGenerateRequest) -> Dict[str, Any]:
        """
        Algorithmic / AI-assisted diet plan generator that constructs balanced,
        nutrient-aligned meal slots with precise portions.
        """
        cals = payload.target_calories
        goal = payload.goal
        pref = payload.dietary_preference

        # Macro distribution based on goal and preference
        if pref.lower() == "keto":
            p_ratio, c_ratio, f_ratio = 0.25, 0.05, 0.70
        elif goal.lower() in ["fat loss", "cut", "cutting"]:
            p_ratio, c_ratio, f_ratio = 0.35, 0.40, 0.25
        elif goal.lower() in ["muscle gain", "bulk", "hypertrophy"]:
            p_ratio, c_ratio, f_ratio = 0.28, 0.50, 0.22
        else: # Balanced / Maintenance
            p_ratio, c_ratio, f_ratio = 0.30, 0.45, 0.25

        total_p_g = round((cals * p_ratio) / 4.0, 1)
        total_c_g = round((cals * c_ratio) / 4.0, 1)
        total_f_g = round((cals * f_ratio) / 9.0, 1)

        is_veg = "veg" in pref.lower()
        is_keto = "keto" in pref.lower()

        # Generate 4 meals
        meals = []

        # Breakfast (25%)
        b_cals = int(cals * 0.25)
        if is_veg:
            b_foods = [
                {"name": "Paneer Bhurji / Spiced Tofu", "portion": "120g", "calories": int(b_cals * 0.55), "protein": round(total_p_g * 0.25, 1), "carbs": 5.0, "fats": round(total_f_g * 0.28, 1)},
                {"name": "Whole Wheat Toast", "portion": "2 slices", "calories": int(b_cals * 0.35), "protein": 6.0, "carbs": round(total_c_g * 0.25, 1), "fats": 2.0},
                {"name": "Green Tea with Lemon", "portion": "1 cup", "calories": 5, "protein": 0.0, "carbs": 1.0, "fats": 0.0}
            ]
        elif is_keto:
            b_foods = [
                {"name": "Scrambled Eggs in Butter", "portion": "3 large", "calories": int(b_cals * 0.65), "protein": round(total_p_g * 0.26, 1), "carbs": 2.0, "fats": round(total_f_g * 0.30, 1)},
                {"name": "Avocado Slices", "portion": "80g", "calories": int(b_cals * 0.30), "protein": 1.5, "carbs": 3.0, "fats": 12.0}
            ]
        else:
            b_foods = [
                {"name": "Egg Whites + Whole Egg Scramble", "portion": "3 whites + 1 whole", "calories": int(b_cals * 0.45), "protein": round(total_p_g * 0.28, 1), "carbs": 2.0, "fats": 6.0},
                {"name": "Rolled Oats with Berries", "portion": "50g oats + 50g berries", "calories": int(b_cals * 0.50), "protein": 7.0, "carbs": round(total_c_g * 0.28, 1), "fats": 3.0}
            ]
        meals.append({
            "id": "ai_m1",
            "slot_name": "Breakfast",
            "time": "08:00",
            "target_calories": b_cals,
            "target_protein": round(total_p_g * 0.26, 1),
            "target_carbs": round(total_c_g * 0.25, 1),
            "target_fats": round(total_f_g * 0.25, 1),
            "instructions": "High protein kickstarter to elevate morning metabolic rate.",
            "foods": b_foods
        })

        # Lunch (35%)
        l_cals = int(cals * 0.35)
        if is_veg:
            l_foods = [
                {"name": "Sprouted Lentil Curry (Dal)", "portion": "200g", "calories": int(l_cals * 0.45), "protein": round(total_p_g * 0.22, 1), "carbs": 32.0, "fats": 3.0},
                {"name": "Brown Basmati Rice", "portion": "160g cooked", "calories": int(l_cals * 0.35), "protein": 4.5, "carbs": round(total_c_g * 0.35, 1), "fats": 1.5},
                {"name": "Fresh Cucumber & Tomato Salad", "portion": "120g", "calories": 40, "protein": 2.0, "carbs": 8.0, "fats": 0.5}
            ]
        else:
            l_foods = [
                {"name": "Grilled Lemon Herb Chicken Breast", "portion": "175g", "calories": int(l_cals * 0.50), "protein": round(total_p_g * 0.36, 1), "carbs": 0.0, "fats": 5.0},
                {"name": "Steamed Sweet Potato or Brown Rice", "portion": "180g", "calories": int(l_cals * 0.35), "protein": 3.5, "carbs": round(total_c_g * 0.35, 1), "fats": 1.0},
                {"name": "Steamed Asparagus & Bell Peppers", "portion": "140g", "calories": 45, "protein": 3.0, "carbs": 8.0, "fats": 0.5}
            ]
        meals.append({
            "id": "ai_m2",
            "slot_name": "Lunch",
            "time": "13:00",
            "target_calories": l_cals,
            "target_protein": round(total_p_g * 0.34, 1),
            "target_carbs": round(total_c_g * 0.35, 1),
            "target_fats": round(total_f_g * 0.30, 1),
            "instructions": "Main sustained carbohydrate and lean protein meal for midday energy.",
            "foods": l_foods
        })

        # Pre/Post Snack (15%)
        s_cals = int(cals * 0.15)
        meals.append({
            "id": "ai_m3",
            "slot_name": "Afternoon Performance Snack",
            "time": "17:00",
            "target_calories": s_cals,
            "target_protein": round(total_p_g * 0.18, 1),
            "target_carbs": round(total_c_g * 0.18, 1),
            "target_fats": round(total_f_g * 0.15, 1),
            "instructions": "Consume 1 hour before training or as afternoon focus replenishment.",
            "foods": [
                {"name": "Protein Shake or Greek Yogurt", "portion": "1 serving", "calories": int(s_cals * 0.7), "protein": round(total_p_g * 0.18, 1), "carbs": 8.0, "fats": 2.0},
                {"name": "Almonds / Roasted Walnuts", "portion": "15g", "calories": int(s_cals * 0.3), "protein": 3.0, "carbs": 3.0, "fats": 8.0}
            ]
        })

        # Dinner (25%)
        d_cals = int(cals * 0.25)
        if is_veg:
            d_foods = [
                {"name": "Grilled Soya Chunks or Tofu Stir-Fry", "portion": "160g", "calories": int(d_cals * 0.60), "protein": round(total_p_g * 0.26, 1), "carbs": 12.0, "fats": 8.0},
                {"name": "Quinoa & Steamed Broccoli", "portion": "140g", "calories": int(d_cals * 0.35), "protein": 6.0, "carbs": round(total_c_g * 0.22, 1), "fats": 2.5}
            ]
        else:
            d_foods = [
                {"name": "Baked Salmon or White Fish Fillet", "portion": "180g", "calories": int(d_cals * 0.65), "protein": round(total_p_g * 0.26, 1), "carbs": 0.0, "fats": round(total_f_g * 0.28, 1)},
                {"name": "Zucchini Noodles & Sautéed Mushrooms", "portion": "180g", "calories": int(d_cals * 0.25), "protein": 4.0, "carbs": round(total_c_g * 0.18, 1), "fats": 2.0}
            ]
        meals.append({
            "id": "ai_m4",
            "slot_name": "Dinner",
            "time": "20:30",
            "target_calories": d_cals,
            "target_protein": round(total_p_g * 0.22, 1),
            "target_carbs": round(total_c_g * 0.22, 1),
            "target_fats": round(total_f_g * 0.30, 1),
            "instructions": "Light, easily digestible evening meal to promote overnight muscle protein synthesis and quality sleep.",
            "foods": d_foods
        })

        return {
            "title": f"AI {goal} Protocol ({cals} kcal)",
            "description": f"Personalized {goal} protocol tailored for {payload.client_name} with {pref} nutritional guidelines.",
            "dietary_tags": [pref, goal, "AI Generated"],
            "total_calories": cals,
            "protein_g": total_p_g,
            "carbs_g": total_c_g,
            "fats_g": total_f_g,
            "water_liters": round(max(2.5, cals * 0.0015), 1),
            "supplements": ["Daily Multivitamin", "Omega-3 (1000mg)", "Electrolytes in morning water"],
            "instructions": "Follow meal timings consistently within a ±45 minute window. Hydrate between meals, not in large quantities during meals.",
            "meals": meals
        }

    def _recalculate_totals_if_needed(self, data: Dict[str, Any]):
        meals = data.get("meals") or []
        if meals:
            total_cal = 0
            total_p = 0.0
            total_c = 0.0
            total_f = 0.0
            for m in meals:
                m_cal = m.get("target_calories") or 0
                m_p = m.get("target_protein") or 0.0
                m_c = m.get("target_carbs") or 0.0
                m_f = m.get("target_fats") or 0.0
                
                foods = m.get("foods") or []
                if foods and (m_cal == 0 or m_p == 0.0):
                    m_cal = sum(int(f.get("calories") or 0) for f in foods)
                    m_p = sum(float(f.get("protein") or 0.0) for f in foods)
                    m_c = sum(float(f.get("carbs") or 0.0) for f in foods)
                    m_f = sum(float(f.get("fats") or 0.0) for f in foods)
                    m["target_calories"] = m_cal
                    m["target_protein"] = round(m_p, 1)
                    m["target_carbs"] = round(m_c, 1)
                    m["target_fats"] = round(m_f, 1)

                total_cal += m_cal
                total_p += m_p
                total_c += m_c
                total_f += m_f

            if total_cal > 0:
                data["total_calories"] = total_cal
                data["protein_g"] = round(total_p, 1)
                data["carbs_g"] = round(total_c, 1)
                data["fats_g"] = round(total_f, 1)


diet_service = DietService()
