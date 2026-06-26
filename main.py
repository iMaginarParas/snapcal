import os
import uvicorn
from app.main import app

# Expose 'app' at the root module level for ASGI servers to run "main:app"
__all__ = ["app"]

if __name__ == "__main__":
    # Get port from environment variables, fallback to 3000 (Express legacy port)
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
