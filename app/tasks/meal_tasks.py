import requests
import io
import time
import sentry_sdk
from ..celery_app import celery
from ..models.meal import Meal
from ..database import SessionLocal
from ..utils.ai_utils import food_detector
from ..services.analytics_service import track_event, is_feature_enabled
from ..services.notification_service import notify_user
from ..services.metrics_service import track_ai_job, record_metric

def process_meal(meal_id, image_url):
    db = SessionLocal()
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        db.close()
        return

    try:
        # Fetch image bytes from Supabase URL (or local path if simulated)
        if image_url.startswith("http"):
            response = requests.get(image_url)
            response.raise_for_status()
            image_bytes = response.content
        else:
            # Handle local file if provided as a path
            with open(image_url, "rb") as f:
                image_bytes = f.read()

        # Perform AI analysis
        start_time = time.time()
        
        from ..services.vision_service import vision_service
        import asyncio
        
        # Try real AI (Gemini)
        result = None
        try:
            result = asyncio.run(vision_service.analyze_meal(image_bytes))
        except Exception as e:
            print(f"Gemini Analysis Failed, falling back: {e}")

        # Fallback to Mock/Classifier if needed
        if not result:
            result = food_detector.predict(image_bytes)
            model_used = "mobilenet_v3_fallback"
        else:
            model_used = "gemini-1.5-flash"
            
        duration = time.time() - start_time
        
        # Track AI job metric
        track_ai_job(model_name=model_used, duration_sec=duration)
        
        # Update meal record in database
        meal.food_name = result.get("food_name", "Unknown Food")
        meal.calories = result.get("calories", 0)
        meal.protein = result.get("protein", 0)
        meal.carbs = result.get("carbs", 0)
        meal.fat = result.get("fat", 0)
        meal.portion_size = result.get("portion_size", "1 serving")
        meal.status = "completed"
        db.commit()

        # Track successful processing analytics
        track_event(
            user_id=meal.user_id,
            event_name="meal_processed",
            properties={
                "food_name": meal.food_name,
                "calories": meal.calories,
                "processing_time": duration
            }
        )

        # Trigger Push Notification if feature flag is enabled
        if is_feature_enabled(user_id=meal.user_id, flag_name="enable_push_notifications"):
            notify_user(
                user_id=meal.user_id,
                title="Meal Analysis Ready 🥗",
                body=f"Your {meal.food_name} contains {meal.calories} calories.",
                data={"meal_id": str(meal.id)},
                db=db
            )

        print(f"Meal {meal_id} processed successfully: {meal.food_name}")

    except Exception as exc:
        db.rollback()
        # Track job failure
        record_metric("ai_job_failed", tags={"error": str(exc)})
        
        # Capture exception to Sentry before retrying
        sentry_sdk.capture_exception(exc)
        
        # Track processing failure analytics
        track_event(
            user_id=meal.user_id,
            event_name="meal_processing_failed",
            properties={"error": str(exc)}
        )
        
        print(f"Error processing meal {meal_id}: {str(exc)}")
    finally:
        db.close()
