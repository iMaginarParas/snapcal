from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import NotFoundException, UnauthorizedException, BadRequestException
import traceback
from app.core.logging import logger

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(NotFoundException)
    async def not_found_handler(request: Request, exc: NotFoundException):
        return JSONResponse(status_code=exc.status_code, content={"success": False, "detail": exc.detail})

    @app.exception_handler(UnauthorizedException)
    async def unauthorized_handler(request: Request, exc: UnauthorizedException):
        return JSONResponse(status_code=exc.status_code, content={"success": False, "detail": exc.detail})

    @app.exception_handler(BadRequestException)
    async def bad_request_handler(request: Request, exc: BadRequestException):
        return JSONResponse(status_code=exc.status_code, content={"success": False, "detail": exc.detail})

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"success": False, "detail": str(exc)})
