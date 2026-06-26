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
            summary["calories"] += int(meal.get("total_calories") or meal.get("calories") or 0)
            summary["protein"] += float(meal.get("protein") or 0.0)
            summary["carbs"] += float(meal.get("carbs") or 0.0)
            summary["fat"] += float(meal.get("fat") or meal.get("fats") or 0.0)
            summary["fiber"] += float(meal.get("fiber") or 0.0)
            summary["meals"].append({
                "id": meal.get("id"),
                "name": meal.get("name"),
                "calories": meal.get("total_calories") or meal.get("calories") or 0,
                "meal_type": meal.get("meal_type") or "Other",
                "logged_at": meal.get("logged_at")
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
