from ..celery_app import celery
from ..models.meal import Meal
from ..database import SessionLocal
from ..services.storage_service import supabase, bucket
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@celery.task
def cleanup_old_images():
    """
    Deletes images and records older than 90 days to save costs.
    """
    db = SessionLocal()
    try:
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        # Find old meals
        old_meals = db.query(Meal).filter(Meal.created_at < ninety_days_ago).all()
        
        deleted_count = 0
        for meal in old_meals:
            try:
                # 1. Delete from Supabase Storage
                # image_url format is usually .../bucket/meals/filename.jpg
                if meal.image_url and "meals/" in meal.image_url:
                    path = "meals/" + meal.image_url.split("meals/")[-1]
                    supabase.storage.from_(bucket).remove([path])
                
                # 2. Delete from DB
                db.delete(meal)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to cleanup meal {meal.id}: {str(e)}")
        
        db.commit()
        logger.info(f"COST OPTIMIZATION: Cleaned up {deleted_count} old images and records.")
        
        from ..services.metrics_service import record_metric
        record_metric("images_cleaned_up", value=float(deleted_count))
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        db.rollback()
    finally:
        db.close()
