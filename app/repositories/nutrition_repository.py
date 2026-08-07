from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.repositories.meal_repository import meal_repository

class NutritionRepository:
    def get_daily_summary(self, user_id: str, date_str: str) -> Dict[str, Any]:
        """Calculates total macros and calories consumed on a specific date."""
        meals = meal_repository.get_meals_by_date(user_id, date_str)
        
        summary = {
            "date": date_str,
            "calories": 0,
            "protein": 0.0,
            "carbs": 0.0,
            "fat": 0.0,
            "fiber": 0.0,
            "meal_count": len(meals),
            "meals": []
        }

        for meal in meals:
            food_items = meal.get("food_items") or []

            m_calories = int(meal.get("total_calories") or meal.get("calories") or 0)
            m_protein = float(meal.get("protein") or 0.0)
            m_carbs = float(meal.get("carbs") or 0.0)
            m_fat = float(meal.get("fat") or meal.get("fats") or 0.0)
            m_fiber = float(meal.get("fiber") or 0.0)
            m_name = (meal.get("name") or "").strip()

            # Fallback to food_items if parent totals are 0 or empty
            if (m_calories == 0 or m_protein == 0.0) and food_items:
                fi_cal = sum(int(fi.get("calories") or 0) for fi in food_items)
                fi_prot = sum(float(fi.get("protein") or 0.0) for fi in food_items)
                fi_carbs = sum(float(fi.get("carbs") or 0.0) for fi in food_items)
                fi_fat = sum(float(fi.get("fat") or fi.get("fats") or 0.0) for fi in food_items)
                fi_fiber = sum(float(fi.get("fiber") or 0.0) for fi in food_items)
                
                if fi_cal > 0:
                    m_calories = fi_cal
                if fi_prot > 0:
                    m_protein = fi_prot
                if fi_carbs > 0:
                    m_carbs = fi_carbs
                if fi_fat > 0:
                    m_fat = fi_fat
                if fi_fiber > 0:
                    m_fiber = fi_fiber

            if not m_name or m_name.lower() in ["meal log", "analyzed meal", "unknown meal", "analyzed food"]:
                if food_items:
                    first_fn = food_items[0].get("food_name") or food_items[0].get("normalized_name") or food_items[0].get("name")
                    if first_fn:
                        m_name = first_fn

            summary["calories"] += m_calories
            summary["protein"] += m_protein
            summary["carbs"] += m_carbs
            summary["fat"] += m_fat
            summary["fiber"] += m_fiber

            summary["meals"].append({
                "id": meal.get("id"),
                "name": m_name or "Meal Log",
                "calories": m_calories,
                "total_calories": m_calories,
                "protein": round(m_protein, 1),
                "carbs": round(m_carbs, 1),
                "fat": round(m_fat, 1),
                "fats": round(m_fat, 1),
                "fiber": round(m_fiber, 1),
                "meal_type": meal.get("meal_type") or "Other",
                "logged_at": meal.get("logged_at"),
                "image_url": meal.get("image_url"),
                "food_items": food_items
            })

        summary["protein"] = round(summary["protein"], 1)
        summary["carbs"] = round(summary["carbs"], 1)
        summary["fat"] = round(summary["fat"], 1)
        summary["fiber"] = round(summary["fiber"], 1)

        return summary

    def get_weekly_summary(self, user_id: str, end_date_str: str = None) -> Dict[str, Any]:
        """Calculates macro metrics and daily averages for the past 7 days."""
        if not end_date_str:
            end_date = datetime.utcnow().date()
        else:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            
        start_date = end_date - timedelta(days=6)
        
        days_data = []
        total_calories = 0
        total_protein = 0.0
        total_carbs = 0.0
        total_fat = 0.0
        total_fiber = 0.0
        logged_days = 0

        for i in range(7):
            current_date = start_date + timedelta(days=i)
            curr_date_str = current_date.strftime("%Y-%m-%d")
            
            day_sum = self.get_daily_summary(user_id, curr_date_str)
            days_data.append({
                "date": curr_date_str,
                "calories": day_sum["calories"],
                "protein": day_sum["protein"],
                "carbs": day_sum["carbs"],
                "fat": day_sum["fat"],
                "fiber": day_sum["fiber"]
            })
            
            if day_sum["meal_count"] > 0:
                logged_days += 1
                total_calories += day_sum["calories"]
                total_protein += day_sum["protein"]
                total_carbs += day_sum["carbs"]
                total_fat += day_sum["fat"]
                total_fiber += day_sum["fiber"]

        days_count = max(logged_days, 1)

        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "average_calories": int(total_calories / 7), # Average over all 7 days
            "average_protein": round(total_protein / 7, 1),
            "average_carbs": round(total_carbs / 7, 1),
            "average_fat": round(total_fat / 7, 1),
            "average_fiber": round(total_fiber / 7, 1),
            "days": days_data
        }

nutrition_repository = NutritionRepository()
