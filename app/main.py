from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.middleware.cors import add_cors_middleware
from app.middleware.errors import add_exception_handlers

# Import routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router, users_plural_router
from app.api.workouts import router as workouts_router
from app.api.health import router as health_router
from app.api.fasting import router as fasting_router
from app.api.groups import router as groups_router
from app.api.analytics import router as analytics_router
from app.api.meals import router as meals_router
from app.api.steps import router as steps_router
from app.api.supplements import router as supplements_router
from app.api.referrals import router as referrals_router
from app.api.friends import router as friends_router
from app.api.exports import router as exports_router
from app.api.support import router as support_router
from app.api.badges import router as badges_router
from app.api.dm import router as dm_router


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Clean Architecture FastAPI Backend for SABTRACK AI"
)

# Add Middlewares
add_cors_middleware(app)
add_exception_handlers(app)

from fastapi.responses import FileResponse, HTMLResponse

# Ensure uploads and static folders exist and mount static files
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "../uploads")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/delete-account", response_class=HTMLResponse)
@app.get("/delete-account.html", response_class=HTMLResponse)
def serve_delete_account_page():
    html_path = os.path.join(STATIC_DIR, "delete-account.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("<h1>Delete Account Page</h1>")


@app.get("/privacy", response_class=HTMLResponse)
@app.get("/privacy.html", response_class=HTMLResponse)
def serve_privacy_page():
    html_path = os.path.join(STATIC_DIR, "privacy.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("<h1>Privacy Policy Page</h1>")


# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(users_plural_router, prefix=settings.API_V1_STR)
app.include_router(workouts_router, prefix=settings.API_V1_STR)
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(fasting_router, prefix=settings.API_V1_STR)
app.include_router(groups_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(meals_router, prefix=settings.API_V1_STR)
app.include_router(steps_router, prefix=settings.API_V1_STR)
app.include_router(supplements_router, prefix=settings.API_V1_STR)
app.include_router(referrals_router, prefix=settings.API_V1_STR)
app.include_router(friends_router, prefix=settings.API_V1_STR)
app.include_router(exports_router, prefix=settings.API_V1_STR)
app.include_router(support_router, prefix=settings.API_V1_STR)
app.include_router(badges_router, prefix=settings.API_V1_STR)
app.include_router(dm_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
