from typing import Optional
from datetime import datetime
import json
import os
import google.generativeai as genai
from app.repositories.db_repository import db_repository

def _get_active_gemini_model():
    key = os.getenv("GEMINI_API_KEY") or ""
    if key and key != "your_gemini_api_key_here" and "placeholder" not in key.lower():
        try:
            genai.configure(api_key=key)
            for m in ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-1.5-flash", "gemini-2.0-flash"]:
                try:
                    model = genai.GenerativeModel(m)
                    return model
                except Exception:
                    continue
        except Exception:
            pass
    return None

class AnalyticsService:
    def get_insights(self, user_id: str) -> dict:
        """Returns personalized AI Coach daily motivation & nutrition tips."""
        try:
            model = _get_active_gemini_model()
            if model:
                today_str = datetime.utcnow().isoformat().split("T")[0]
                meals = db_repository.get_meals(user_id, today_str) or []
                stats = db_repository.get_daily_stats(user_id, today_str) or {"steps": 0}
                
                cal = sum(m.get("total_calories") or m.get("calories") or 0 for m in meals)
                steps = stats.get("steps", 0)

                prompt = f"""You are Sabtrack AI Health & Fitness Coach. 
                User stats today: {steps} steps taken, {cal} calories consumed from {len(meals)} logged meals.
                Provide ONE short, highly encouraging, action-oriented 1-2 sentence fitness/nutrition coaching tip. Do not use markdown formatting."""

                res = model.generate_content(prompt)
                if res and res.text:
                    return {"success": True, "data": {"insight": res.text.strip()}}
        except Exception as e:
            print(f"[AnalyticsService] AI Insight warning: {e}")

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

        # Try live Gemini AI Coach generation
        try:
            model = _get_active_gemini_model()
            if model:
                prompt = f"""You are Sabtrack AI Health & Fitness Coach. Analyze this user's daily metrics for date {date_str}:
                - Calories Consumed: {calorie_intake} kcal (Protein: {protein_intake}g, Carbs: {carbs_intake}g, Fats: {fats_intake}g)
                - Calories Burned: {calorie_burned} kcal (Steps: {steps}, Workouts: {len(workouts)})
                - Water Hydration: {water} ml
                
                Generate a JSON object with 3 keys:
                "summary": A 1-sentence overall coaching summary for the day.
                "didBetter": A 1-sentence highlight of what the user did well today.
                "toImprove": A 1-sentence actionable tip for tomorrow.
                Return ONLY raw valid JSON."""

                res = model.generate_content(prompt)
                if res and res.text:
                    cleaned = res.text.strip().replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(cleaned)
                    summary = parsed.get("summary") or summary
                    did_better = parsed.get("didBetter") or did_better
                    to_improve = parsed.get("toImprove") or to_improve
        except Exception as e:
            print(f"[AnalyticsService] AI Daily Report warning: {e}")

        if steps > 8000 and "Exceptional" not in did_better:
            did_better = f"Exceptional step count ({steps} steps)! You were highly active today, supporting cardiovascular recovery."

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
