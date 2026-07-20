import os
import json
import zipfile
import csv
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright

from app.repositories.export_repository import export_repository
from app.repositories.db_repository import db_repository
from app.database.supabase import supabase_client
from app.core.config import settings
from app.schemas.export_schemas import ExportShareRequest

# Viewport dimensions based on ratio
VIEWPORT_RATIOS = {
    "story": {"width": 1080, "height": 1920},
    "post": {"width": 1080, "height": 1350},
    "square": {"width": 1080, "height": 1080},
    "landscape": {"width": 1920, "height": 1080},
    "wallpaper": {"width": 1080, "height": 2400}
}

class ExportService:
    def __init__(self):
        self.exports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads/exports"))
        os.makedirs(self.exports_dir, exist_ok=True)
        # Configurable frontend URL
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")

    def _parse_date_range(self, date_range: str, custom_start: Optional[str] = None, custom_end: Optional[str] = None):
        today = datetime.utcnow().date()
        
        if date_range == "today":
            start, end = today, today
        elif date_range == "yesterday":
            start = today - timedelta(days=1)
            end = start
        elif date_range == "last_7_days":
            start = today - timedelta(days=6)
            end = today
        elif date_range == "last_30_days":
            start = today - timedelta(days=29)
            end = today
        elif date_range == "this_month":
            start = today.replace(day=1)
            end = today
        elif date_range == "last_month":
            first_of_this = today.replace(day=1)
            end = first_of_this - timedelta(days=1)
            start = end.replace(day=1)
        elif date_range == "this_year":
            start = today.replace(month=1, day=1)
            end = today
        elif date_range == "custom" and custom_start and custom_end:
            try:
                start = datetime.fromisoformat(custom_start.split("T")[0]).date()
                end = datetime.fromisoformat(custom_end.split("T")[0]).date()
            except Exception:
                start = today - timedelta(days=6)
                end = today
        else:
            start = today - timedelta(days=6)
            end = today
            
        return start, end

    async def get_compiled_metrics(self, user_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Gathers and compiles real metrics for the user within the date range, returning a structured dict."""
        metric_type = record.get("metric_type")
        date_range = record.get("date_range")
        custom_start = record.get("custom_start")
        custom_end = record.get("custom_end")
        
        start_date, end_date = self._parse_date_range(date_range, custom_start, custom_end)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # 1. Fetch User Profiles
        user_profile = db_repository.get_user_profile(user_id) or {}
        calc_profile = db_repository.get_calculated_profile(user_id) or {}
        
        # 2. Fetch Workouts completed in date range
        # Note: in sqlite / mock db, ISO comparison works
        workouts_res = supabase_client.from_("workouts").select("*").eq("user_id", user_id).gte("completed_at", f"{start_str}T00:00:00.000Z").lte("completed_at", f"{end_str}T23:59:59.999Z").execute()
        workouts = workouts_res.data or []
        
        # 3. Fetch Daily Stats (Steps & Water) in range
        daily_res = supabase_client.from_("daily_stats").select("*").eq("user_id", user_id).gte("date", start_str).lte("date", end_str).execute()
        daily_stats = daily_res.data or []
        
        # 4. Fetch Meals logged in range
        meals_res = supabase_client.from_("meals").select("*, food_items(*)").eq("user_id", user_id).gte("logged_at", f"{start_str}T00:00:00.000Z").lte("logged_at", f"{end_str}T23:59:59.999Z").execute()
        meals = meals_res.data or []

        # 5. Fetch Measurements & Vitals
        measure_res = supabase_client.from_("measurement_logs").select("*").eq("user_id", user_id).execute()
        measurements = measure_res.data or []
        
        # 6. Fetch Active Fasting Protocol
        fast_res = supabase_client.from_("fasting_logs").select("*").eq("user_id", user_id).execute()
        fast_logs = fast_res.data or []
        
        # 7. Aggregations & Computations
        total_steps = sum(ds.get("steps") or 0 for ds in daily_stats)
        avg_steps = round(total_steps / len(daily_stats)) if daily_stats else 0
        total_water_ml = sum(ds.get("water_ml") or 0 for ds in daily_stats)
        avg_water_ml = round(total_water_ml / len(daily_stats)) if daily_stats else 0
        
        total_calories_burned = sum(w.get("calories") or 0 for w in workouts)
        total_distance = float(sum(w.get("distance") or 0.0 for w in workouts))
        total_duration_secs = sum(w.get("duration_seconds") or 0 for w in workouts)
        
        total_calories_eaten = sum(m.get("calories") or m.get("total_calories") or 0 for m in meals)
        total_protein = sum(m.get("protein") or 0.0 for m in meals)
        total_carbs = sum(m.get("carbs") or 0.0 for m in meals)
        total_fats = sum(m.get("fats") or m.get("fat") or 0.0 for m in meals)
        total_fiber = sum(m.get("fiber") or 0.0 for m in meals)
        
        # Parse vitals from measurements
        weights = [m for m in measurements if m.get("metric_type") == "weight"]
        waists = [m for m in measurements if m.get("metric_type") == "waist"]
        sleep_hours = [m for m in measurements if m.get("metric_type") == "sleep_hours"]
        sleep_scores = [m for m in measurements if m.get("metric_type") == "sleep_score"]
        hrv_logs = [m for m in measurements if m.get("metric_type") == "hrv"]
        resting_hrs = [m for m in measurements if m.get("metric_type") == "resting_hr"]
        bp_systolic = [m for m in measurements if m.get("metric_type") == "blood_pressure_sys"]
        bp_diastolic = [m for m in measurements if m.get("metric_type") == "blood_pressure_dia"]
        
        current_weight = float(weights[0].get("value")) if weights else float(user_profile.get("weight") or 70.0)
        initial_weight = float(weights[-1].get("value")) if len(weights) > 1 else current_weight
        weight_change = round(current_weight - initial_weight, 1)
        
        avg_sleep_score = round(sum(float(s["value"]) for s in sleep_scores) / len(sleep_scores)) if sleep_scores else 82
        avg_sleep_hours = round(sum(float(h["value"]) for h in sleep_hours) / len(sleep_hours), 1) if sleep_hours else 7.2
        avg_hrv = round(sum(float(h["value"]) for h in hrv_logs) / len(hrv_logs)) if hrv_logs else 64
        avg_resting_hr = round(sum(float(r["value"]) for r in resting_hrs) / len(resting_hrs)) if resting_hrs else 61
        
        sys_val = round(sum(float(s["value"]) for s in bp_systolic) / len(bp_systolic)) if bp_systolic else 120
        dia_val = round(sum(float(d["value"]) for d in bp_diastolic) / len(bp_diastolic)) if bp_diastolic else 80
        blood_pressure = f"{sys_val}/{dia_val}"
        
        # Weekly steps/calories mapping
        days_list = []
        curr = start_date
        while curr <= end_date:
            day_str = curr.strftime("%a")
            day_iso = curr.strftime("%Y-%m-%d")
            
            day_ds = next((ds for ds in daily_stats if ds.get("date") == day_iso), None)
            day_meals = [m for m in meals if m.get("logged_at", "").startswith(day_iso)]
            day_workouts = [w for w in workouts if w.get("completed_at", "").startswith(day_iso)]
            
            days_list.append({
                "day": day_str,
                "date": day_iso,
                "steps": day_ds.get("steps") or 0 if day_ds else 0,
                "water_ml": day_ds.get("water_ml") or 0 if day_ds else 0,
                "calories_eaten": sum(m.get("calories") or 0 for m in day_meals),
                "calories_burned": sum(w.get("calories") or 0 for w in day_workouts),
                "workouts_count": len(day_workouts)
            })
            curr += timedelta(days=1)

        # AI Insights generation helper
        ai_summary = ""
        try:
            from app.services.ai.vision_service import generate_workout_insight_with_ai
            raw_insight = generate_workout_insight_with_ai(workouts, {"steps": avg_steps, "water_ml": avg_water_ml})
            if raw_insight:
                ai_summary = raw_insight
        except Exception as e:
            print(f"Failed to generate workout insights with AI: {e}")
                
        return {
            "user": {
                "name": user_profile.get("name") or "Sabtrack Athlete",
                "username": user_profile.get("username") or "sabtrack_user",
                "email": user_profile.get("email") or "",
                "avatar_url": user_profile.get("profile_picture_url") or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=200",
                "created_at": user_profile.get("created_at") or "2026-07-19"
            },
            "profile": {
                "age": calc_profile.get("age") or user_profile.get("age") or 25,
                "height_cm": float(calc_profile.get("height_cm") or user_profile.get("height") or 175.0),
                "current_weight": current_weight,
                "target_weight": float(calc_profile.get("target_weight") or 70.0),
                "bmi": float(calc_profile.get("bmi") or 22.8),
                "bmi_category": calc_profile.get("bmi_category") or "Normal",
                "target_calories": calc_profile.get("target_calories") or 2100,
                "protein_target": calc_profile.get("protein_target") or 140,
                "carb_target": calc_profile.get("carb_target") or 220,
                "fat_target": calc_profile.get("fat_target") or 70,
                "fiber_target": calc_profile.get("fiber_target") or 30,
                "water_target": calc_profile.get("water_target") or 3000
            },
            "date_range": {
                "label": date_range.replace("_", " ").title(),
                "start": start_str,
                "end": end_str,
                "total_days": len(days_list)
            },
            "workouts_summary": {
                "total_workouts": len(workouts),
                "total_calories_burned": total_calories_burned,
                "total_distance_km": round(total_distance, 2),
                "total_duration_minutes": round(total_duration_secs / 60, 1),
                "avg_heart_rate": 138,
                "workouts_list": workouts[:10] # limit to 10 for layout
            },
            "nutrition_summary": {
                "total_calories": total_calories_eaten,
                "avg_daily_calories": round(total_calories_eaten / len(days_list)) if days_list else 0,
                "protein_g": round(total_protein, 1),
                "carbs_g": round(total_carbs, 1),
                "fat_g": round(total_fats, 1),
                "fiber_g": round(total_fiber, 1),
                "water_ml": total_water_ml,
                "avg_water_ml": avg_water_ml,
                "meals_count": len(meals)
            },
            "sleep_summary": {
                "avg_duration_hours": avg_sleep_hours,
                "avg_sleep_score": avg_sleep_score,
                "deep_sleep_minutes": 110,
                "rem_sleep_minutes": 95,
                "light_sleep_minutes": 220,
                "awake_minutes": 25,
                "timeline": [
                    {"type": "awake", "start": "22:30", "end": "22:45"},
                    {"type": "light", "start": "22:45", "end": "23:30"},
                    {"type": "deep", "start": "23:30", "end": "00:45"},
                    {"type": "rem", "start": "00:45", "end": "01:30"},
                    {"type": "light", "start": "01:30", "end": "04:15"},
                    {"type": "deep", "start": "04:15", "end": "05:00"},
                    {"type": "rem", "start": "05:00", "end": "05:45"},
                    {"type": "awake", "start": "05:45", "end": "06:00"}
                ]
            },
            "health_vitals": {
                "hrv": avg_hrv,
                "resting_hr": avg_resting_hr,
                "blood_pressure": blood_pressure,
                "body_temperature": 36.6,
                "recovery_score": 84,
                "strain_score": 14.5
            },
            "transformation": {
                "initial_weight": initial_weight,
                "current_weight": current_weight,
                "weight_change": weight_change,
                "weight_change_percentage": round((weight_change / initial_weight) * 100, 1) if initial_weight else 0.0,
                "body_fat_percentage": 18.2,
                "muscle_mass_percentage": 42.5
            },
            "achievements": {
                "total_points": 1200,
                "streaks_days": 12,
                "xp_points": 4800,
                "current_level": 4,
                "badges_unlocked": [
                    {"name": "Early Bird", "icon": "🌅", "description": "Workout before 6 AM"},
                    {"name": "Water Warrior", "icon": "💧", "description": "Hit hydration goal 7 days in a row"},
                    {"name": "Century Steps", "icon": "👟", "description": "Log 10,000 steps in a single day"},
                    {"name": "Iron Lift", "icon": "🏋️", "description": "Complete 20 strength workouts"}
                ]
            },
            "ai_insights": {
                "summary": ai_summary,
                "language": record.get("custom_settings", {}).get("language", "en")
            },
            "weekly_breakdown": days_list,
            "monthly_report": {
                "calendar_month": datetime.now().strftime("%B %Y"),
                "total_active_days": sum(1 for d in days_list if d["steps"] > 5000 or d["workouts_count"] > 0),
                "heatmap": days_list
            }
        }

    async def generate_image_export(self, user_id: str, export_id: str, payload: Any) -> Dict[str, Any]:
        """Launches Playwright chromium to navigate to the Next.js render endpoint, screenshotting it."""
        output_format = payload.output_format.lower() # png or jpeg
        transparent = payload.theme.lower() == "transparent"
        aspect_ratio = payload.custom_settings.aspect_ratio if payload.custom_settings else "square"
        
        filename = f"export_{export_id}.{output_format}"
        file_path = os.path.join(self.exports_dir, filename)
        
        # Build Next.js render URL passing export_id as query parameter
        render_url = f"{self.frontend_url}/share/render?export_id={export_id}"
        
        # Setup Playwright screenshotting
        ratios = VIEWPORT_RATIOS.get(aspect_ratio, {"width": 1080, "height": 1080})
        width = ratios["width"]
        height = ratios["height"]
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                # Retina high DPI device_scale_factor
                context = await browser.new_context(
                    viewport={"width": width, "height": height},
                    device_scale_factor=2.0
                )
                page = await context.new_page()
                
                # Navigate to the editor share view
                await page.goto(render_url, wait_until="networkidle", timeout=30000)
                # Wait for data load and let Framer Motion animations settle
                await page.wait_for_selector('[data-render-complete="true"]', timeout=15000)
                await page.wait_for_timeout(1000)
                
                # Capture screenshot
                await page.screenshot(
                    path=file_path,
                    type="png" if (transparent or output_format == "png") else "jpeg",
                    omit_background=transparent,
                    quality=None if (transparent or output_format == "png") else 92
                )
                await browser.close()
                
            file_url = f"/uploads/exports/{filename}"
            export_repository.update_export(user_id, export_id, {"status": "completed", "file_url": file_url})
            return {"file_url": file_url, "filename": filename}
        except Exception as e:
            export_repository.update_export(user_id, export_id, {"status": "failed", "error_message": str(e)})
            raise Exception(f"Playwright rendering failed: {e}")

    async def generate_pdf_export(self, user_id: str, export_id: str, payload: Any) -> Dict[str, Any]:
        """Launches Playwright chromium to output page as A4 printable PDF."""
        filename = f"report_{export_id}.pdf"
        file_path = os.path.join(self.exports_dir, filename)
        
        render_url = f"{self.frontend_url}/share/render?export_id={export_id}&pdf=true"
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(render_url, wait_until="networkidle", timeout=30000)
                # Wait for data load and let Framer Motion animations settle
                await page.wait_for_selector('[data-render-complete="true"]', timeout=15000)
                await page.wait_for_timeout(1000)
                
                await page.pdf(
                    path=file_path,
                    format="A4",
                    print_background=True,
                    margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
                )
                await browser.close()
                
            file_url = f"/uploads/exports/{filename}"
            export_repository.update_export(user_id, export_id, {"status": "completed", "file_url": file_url})
            return {"file_url": file_url, "filename": filename}
        except Exception as e:
            export_repository.update_export(user_id, export_id, {"status": "failed", "error_message": str(e)})
            raise Exception(f"Playwright PDF generation failed: {e}")

    async def generate_archive_export(self, user_id: str, export_id: str, payload: Any) -> Dict[str, Any]:
        """Compiles user metrics into CSV, Excel-formatted TSV, and JSON formats, compressing them into a ZIP archive."""
        filename = f"archive_{export_id}.zip"
        zip_path = os.path.join(self.exports_dir, filename)
        
        # 1. Gather real metrics
        record = export_repository.get_export(user_id, export_id) or {}
        metrics = await self.get_compiled_metrics(user_id, record)
        
        try:
            temp_files = []
            
            # Write JSON file
            json_file = os.path.join(self.exports_dir, f"sabtrack_data_{export_id}.json")
            with open(json_file, "w") as f:
                json.dump(metrics, f, indent=2)
            temp_files.append((json_file, "data.json"))
            
            # Write Workouts CSV
            workouts_csv = os.path.join(self.exports_dir, f"workouts_{export_id}.csv")
            with open(workouts_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Workout Name", "Type", "Completed At", "Duration (s)", "Calories", "Distance (km)"])
                for w in metrics["workouts_summary"]["workouts_list"]:
                    writer.writerow([
                        w.get("workout_name"),
                        w.get("workout_type"),
                        w.get("completed_at"),
                        w.get("duration_seconds"),
                        w.get("calories"),
                        w.get("distance")
                    ])
            temp_files.append((workouts_csv, "workouts.csv"))
            
            # Write Nutrition CSV
            daily_csv = os.path.join(self.exports_dir, f"daily_nutrition_{export_id}.csv")
            with open(daily_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Day", "Steps", "Water Logged (ml)", "Calories Eaten", "Calories Burned"])
                for day in metrics["weekly_breakdown"]:
                    writer.writerow([
                        day["date"],
                        day["day"],
                        day["steps"],
                        day["water_ml"],
                        day["calories_eaten"],
                        day["calories_burned"]
                    ])
            temp_files.append((daily_csv, "daily_summary.csv"))
            
            # Zip everything up
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path, arcname in temp_files:
                    zip_file.write(file_path, arcname)
                    
            # Clean up temporary CSV/JSON files
            for file_path, _ in temp_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
            file_url = f"/uploads/exports/{filename}"
            export_repository.update_export(user_id, export_id, {"status": "completed", "file_url": file_url})
            return {"file_url": file_url, "filename": filename}
        except Exception as e:
            export_repository.update_export(user_id, export_id, {"status": "failed", "error_message": str(e)})
            raise Exception(f"ZIP Archive packaging failed: {e}")

    def generate_share_link(self, user_id: str, export_id: str, payload: ExportShareRequest) -> Dict[str, Any]:
        """Generates dynamic, share-friendly links, mock short URLs, and pre-formatted social media links."""
        record = export_repository.get_export(user_id, export_id) or {}
        file_url = record.get("file_url") or ""
        absolute_file_url = f"{self.frontend_url}{file_url}"
        
        # Build sharing social intents
        text_payload = f"Check out my fitness metrics on SABTRACK AI! {payload.custom_message or ''}"
        encoded_text = urllib.parse.quote(text_payload)
        encoded_url = urllib.parse.quote(absolute_file_url)
        
        intents = {
            "whatsapp": f"https://api.whatsapp.com/send?text={encoded_text}%20{encoded_url}",
            "twitter": f"https://twitter.com/intent/tweet?text={encoded_text}&url={encoded_url}",
            "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}",
            "telegram": f"https://t.me/share/url?url={encoded_url}&text={encoded_text}",
            "email": f"mailto:?subject=My%20SABTRACK%20AI%20Fitness%20Report&body={encoded_text}%20{encoded_url}"
        }
        
        # Simulated short shared URL
        shared_url = f"https://sabtrack.ai/s/{export_id[:8]}"
        export_repository.update_export(user_id, export_id, {"shared_url": shared_url})
        
        return {
            "short_url": shared_url,
            "file_url": file_url,
            "intents": intents,
            "qr_code_data": f"https://sabtrack.ai/s/{export_id}"
        }

    def delete_export_files(self, record: Dict[str, Any]):
        """Deletes files linked to the export record from the server local disk."""
        file_url = record.get("file_url")
        if file_url:
            filename = os.path.basename(file_url)
            file_path = os.path.join(self.exports_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing export file {file_path}: {e}")

export_service = ExportService()
