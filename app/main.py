import os
import time
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

if not os.path.exists("static"):
    os.makedirs("static")

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .database import engine, Base
from .routers import auth, meals, steps, devices, chat, water, progress
from .utils.limiter import limiter
from .services.metrics_service import track_api_request

# Cost Optimization: Reduce log volume by setting default level to WARNING
logging.basicConfig(level=logging.WARNING)

# Import all models to ensure they are registered for create_all
from .models.user import User
from .models.meal import Meal
from .models.step import Step
from .models.device_token import DeviceToken
from .models.chat import ChatMessage
from .models.water import Water
from .models.progress import ProgressPhoto

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        FastApiIntegration(),
    ],
    traces_sample_rate=1.0,
    environment="production",
)

# Create tables
Base.metadata.create_all(bind=engine)

# Safety check for missing columns (manual migration)
from sqlalchemy import text
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_pro BOOLEAN DEFAULT FALSE"))
        conn.commit()
    except Exception as e:
        print(f"Migration notice (is_pro): {e}")


app = FastAPI(title="FitSnap AI API")

# Add Rate Limiter state and middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Middleware to inject security headers into every response.
    """
    response = await call_next(request)
    # Prevent browsers from incorrectly detecting non-scripts as scripts
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    # Enforce HTTPS
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Restrict resource loading locations
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline';"
    return response

@app.middleware("http")
async def profile_request_latency(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    
    track_api_request(
        endpoint=request.url.path,
        status_code=response.status_code,
        response_time=process_time
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    # 10MB limit
    max_size = 10 * 1024 * 1024
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_size:
        return JSONResponse(
            status_code=413,
            content={"detail": "File too large. Maximum size is 10MB."}
        )
    return await call_next(request)

# Route includes
app.include_router(auth.router)
app.include_router(meals.router)
app.include_router(steps.router)
app.include_router(devices.router)
app.include_router(chat.router)
app.include_router(water.router)
app.include_router(progress.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
@limiter.limit("100/minute")
async def health(request: Request):
    return {
        "status": "ok",
        "service": "fitsnap-api"
    }

@app.get("/test-error")
def trigger_error():
    raise Exception("Sentry test error")

@app.get("/")
def read_root():
    return {"message": "FitSnap AI API Running"}
