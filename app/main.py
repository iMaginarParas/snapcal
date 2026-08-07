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
from app.api.notifications import router as notifications_router


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


@app.get("/join-group", response_class=HTMLResponse)
@app.get("/api/join-group", response_class=HTMLResponse)
def serve_join_group_landing_page(code: str = ""):
    app_url = f"sabtrack://join-group?code={code}" if code else "sabtrack://join-group"
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Join Group - SABTRACK AI</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background: #0F172A; color: #F8FAFC; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }}
        .card {{ background: #1E293B; border: 1px solid #334155; border-radius: 24px; padding: 32px; max-width: 420px; width: 100%; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }}
        .icon {{ width: 64px; height: 64px; background: #007AFF; border-radius: 20px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px; font-size: 32px; }}
        h1 {{ font-size: 22px; font-weight: 800; margin-bottom: 8px; color: #FFFFFF; }}
        p {{ font-size: 14px; color: #94A3B8; margin-bottom: 24px; line-height: 1.5; }}
        .code-box {{ background: #0F172A; border: 1px dashed #334155; border-radius: 14px; padding: 12px; font-size: 16px; font-weight: 700; color: #38BDF8; letter-spacing: 1px; margin-bottom: 24px; word-break: break-all; }}
        .btn {{ display: block; width: 100%; padding: 14px; border-radius: 14px; font-size: 15px; font-weight: 700; text-decoration: none; border: none; cursor: pointer; transition: all 0.2s; margin-bottom: 12px; }}
        .btn-primary {{ background: #007AFF; color: #FFFFFF; }}
        .btn-primary:hover {{ background: #0056B3; }}
        .btn-secondary {{ background: #334155; color: #F8FAFC; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🚀</div>
        <h1>Group Invitation</h1>
        <p>You've been invited to join a fitness group on <strong>SABTRACK AI</strong>!</p>
        {'<div class="code-box">Group Code: ' + code + '</div>' if code else ''}
        <a href="{app_url}" class="btn btn-primary">Open in SABTRACK App</a>
        {'<button onclick="navigator.clipboard.writeText(\'' + code + '\'); alert(\'Group code copied to clipboard!\');" class="btn btn-secondary">Copy Group Code</button>' if code else ''}
    </div>
    <script>
        // Automatic deep-link redirect attempt
        if ("{code}") {{
            setTimeout(function() {{
                window.location.href = "{app_url}";
            }}, 400);
        }}
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


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
app.include_router(notifications_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
