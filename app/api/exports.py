from fastapi import APIRouter, Depends, Query, Request, HTTPException
from typing import Optional
from app.schemas.export_schemas import ExportCreateRequest, ExportShareRequest
from app.repositories.export_repository import export_repository
from app.services.exports.export_service import export_service
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/exports", tags=["Export & Share Studio"])

@router.post("/image")
async def export_image(
    payload: ExportCreateRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # 1. Store export log in DB (status pending)
    db_payload = {
        "metric_type": payload.metric_type,
        "date_range": payload.date_range,
        "custom_start": payload.custom_start,
        "custom_end": payload.custom_end,
        "layout_type": payload.layout_type,
        "output_format": payload.output_format,
        "theme": payload.theme,
        "custom_settings": payload.custom_settings.dict() if payload.custom_settings else {},
        "status": "pending"
    }
    export_record = export_repository.create_export(user_id, db_payload)
    export_id = export_record["id"]
    
    # 2. Log audit
    export_repository.log_audit(user_id, "create_image", export_id, ip, user_agent, {"layout": payload.layout_type})
    
    # 3. Trigger image generation (synchronously or asynchronously based on preference, let's process it)
    try:
        result = await export_service.generate_image_export(user_id, export_id, payload)
        return {"success": True, "data": result}
    except Exception as e:
        export_repository.update_export(user_id, export_id, {"status": "failed", "error_message": str(e)})
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/pdf")
async def export_pdf(
    payload: ExportCreateRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    db_payload = {
        "metric_type": payload.metric_type,
        "date_range": payload.date_range,
        "custom_start": payload.custom_start,
        "custom_end": payload.custom_end,
        "layout_type": payload.layout_type,
        "output_format": "pdf",
        "theme": payload.theme,
        "custom_settings": payload.custom_settings.dict() if payload.custom_settings else {},
        "status": "pending"
    }
    export_record = export_repository.create_export(user_id, db_payload)
    export_id = export_record["id"]
    
    export_repository.log_audit(user_id, "create_pdf", export_id, ip, user_agent, {"layout": payload.layout_type})
    
    try:
        result = await export_service.generate_pdf_export(user_id, export_id, payload)
        return {"success": True, "data": result}
    except Exception as e:
        export_repository.update_export(user_id, export_id, {"status": "failed", "error_message": str(e)})
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/share/{export_id}")
async def export_share(
    export_id: str,
    payload: ExportShareRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    record = export_repository.get_export(user_id, export_id)
    if not record:
        raise HTTPException(status_code=404, detail="Export record not found")
        
    export_repository.log_audit(user_id, f"share_{payload.platform}", export_id, ip, user_agent, {"message": payload.custom_message})
    
    shared_data = export_service.generate_share_link(user_id, export_id, payload)
    return {"success": True, "data": shared_data}

@router.post("/archive")
async def export_archive(
    payload: ExportCreateRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    db_payload = {
        "metric_type": payload.metric_type,
        "date_range": payload.date_range,
        "custom_start": payload.custom_start,
        "custom_end": payload.custom_end,
        "layout_type": payload.layout_type,
        "output_format": "zip",
        "theme": payload.theme,
        "custom_settings": payload.custom_settings.dict() if payload.custom_settings else {},
        "status": "pending"
    }
    export_record = export_repository.create_export(user_id, db_payload)
    export_id = export_record["id"]
    
    export_repository.log_audit(user_id, "create_archive", export_id, ip, user_agent)
    
    try:
        result = await export_service.generate_archive_export(user_id, export_id, payload)
        return {"success": True, "data": result}
    except Exception as e:
        export_repository.update_export(user_id, export_id, {"status": "failed", "error_message": str(e)})
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history")
def get_export_history(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_favorite: Optional[bool] = Query(None),
    user_id: str = Depends(get_current_user_id)
):
    history = export_repository.get_exports_history(user_id, offset, limit, is_favorite)
    return {"success": True, "data": history}

@router.delete("/{export_id}")
def delete_export_record(
    export_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    record = export_repository.get_export(user_id, export_id)
    if not record:
        raise HTTPException(status_code=404, detail="Export not found")
        
    export_service.delete_export_files(record)
    export_repository.delete_export(user_id, export_id)
    export_repository.log_audit(user_id, "delete_export", export_id, ip, user_agent)
    
    return {"success": True}

@router.post("/{export_id}/favorite")
def toggle_favorite_export(
    export_id: str,
    user_id: str = Depends(get_current_user_id)
):
    record = export_repository.get_export(user_id, export_id)
    if not record:
        raise HTTPException(status_code=404, detail="Export not found")
        
    new_fav = not record.get("is_favorite", False)
    updated = export_repository.update_export(user_id, export_id, {"is_favorite": new_fav})
    return {"success": True, "data": updated}

@router.get("/render-data/{export_id}")
async def get_export_render_data(export_id: str):
    # This route is loaded by Playwright to fetch raw database metrics for screenshotting
    # It queries by the unique, random export UUID
    record = supabase_client.from_("exports").select("*").eq("id", export_id).maybe_single().execute().data
    if not record:
        raise HTTPException(status_code=404, detail="Render metadata not found")
        
    user_id = record["user_id"]
    metrics = await export_service.get_compiled_metrics(user_id, record)
    return {
        "success": True,
        "data": metrics,
        "theme": record.get("theme"),
        "layout_type": record.get("layout_type"),
        "custom_settings": record.get("custom_settings") or {}
    }

@router.get("/compile-metrics")
async def get_compiled_metrics_endpoint(
    metric_type: str = "health",
    date_range: str = "last_7_days",
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    record = {
        "metric_type": metric_type,
        "date_range": date_range,
        "custom_start": custom_start,
        "custom_end": custom_end
    }
    metrics = await export_service.get_compiled_metrics(user_id, record)
    return {"success": True, "data": metrics}
