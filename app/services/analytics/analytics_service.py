from typing import Optional
from datetime import datetime
from app.repositories.db_repository import db_repository

class AnalyticsService:
    def get_insights(self, user_id: str) -> dict:
        return {"success": True, "data": {"insight": "Consistency is your superpower! Maintain your healthy streaks to build momentum."}}

    def get_daily_report(self, user_id: str, date: Optional[str]) -> dict:
        date_str = date or datetime.utcnow().isoformat().split("T")[0]
        
        # 1. Fetch meals
        meals = db_repository.get_meals(user_id, date_str) or []
        
        # 2. Fetch workouts
        workouts = db_repository.get_workouts(user_id, date_str) or []
        
        # 3. Fetch daily stats
        stats = db_repository.get_daily_stats(user_id, date_str) or {"steps": 0, "water_ml": 0}

        calorie_intake = sum(m.get("total_calories") or m.get("calories") or 0 for m in meals)
        protein_intake = sum(m.get("protein") or 0 for m in meals)
        carbs_intake = sum(m.get("carbs") or 0 for m in meals)
        fats_intake = sum(m.get("fat") or m.get("fats") or 0 for m in meals)

        steps = stats.get("steps", 0)
        water = stats.get("water_ml", 0)

        steps_burn = int(steps * 0.04)
        workout_burn = sum(w.get("calories", 0) for w in workouts)
        calorie_burned = steps_burn + workout_burn

        summary = "Solid consistency today. Keep scanning and tracking your nutrition plates daily."
        did_better = "Hydrated well today and consistently logged your metrics."
        to_improve = "Aim for a higher protein intake tomorrow and try hitting your daily step targets."

        if steps > 8000:
            did_better = "Exceptional step count! You were highly active today, which supports cardiovascular recovery."
        if calorie_intake > 0:
            if calorie_intake > 2500:
                to_improve = "Calorie intake is slightly high. Tomorrow, focus on high-protein options that keep you fuller longer."
                summary = "Today was a high energy intake day. Focus on balancing it with more physical activities."
            else:
                summary = "Excellent portion control! Your calorie levels are perfectly within healthy guidelines."

        return {
            "success": True,
            "data": {
                "date": date_str,
                "calorieIntake": calorie_intake,
                "proteinIntake": round(protein_intake, 1),
                "carbsIntake": round(carbs_intake, 1),
                "fatsIntake": round(fats_intake, 1),
                "calorieBurned": calorie_burned,
                "stepsCalorieBurn": steps_burn,
                "workoutsCalorieBurn": workout_burn,
                "steps": steps,
                "waterMl": water,
                "meals": meals,
                "workouts": workouts,
                "aiReport": {
                    "summary": summary,
                    "didBetter": did_better,
                    "toImprove": to_improve
                }
            }
        }

analytics_service = AnalyticsService()
