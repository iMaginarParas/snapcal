from typing import Dict, Any, List, Optional
from app.database.supabase import supabase_client
from datetime import datetime

class ExportRepository:
    def get_export(self, user_id: str, export_id: str) -> Optional[Dict[str, Any]]:
        res = supabase_client.from_("exports").select("*").eq("id", export_id).eq("user_id", user_id).maybe_single().execute()
        return res.data if res else None

    def create_export(self, user_id: str, export_data: Dict[str, Any]) -> Dict[str, Any]:
        export_data["user_id"] = user_id
        if "created_at" not in export_data:
            export_data["created_at"] = datetime.utcnow().isoformat() + "Z"
        res = supabase_client.from_("exports").insert(export_data).execute()
        return res.data[0] if (res and res.data) else {}

    def update_export(self, user_id: str, export_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("exports").update(updates).eq("id", export_id).eq("user_id", user_id).execute()
        return res.data[0] if (res and res.data) else {}

    def delete_export(self, user_id: str, export_id: str) -> bool:
        res = supabase_client.from_("exports").delete().eq("id", export_id).eq("user_id", user_id).execute()
        # Mock database deletes return boolean directly or length check
        return bool(res.data) if res else False

    def get_exports_history(
        self, 
        user_id: str, 
        offset: int = 0, 
        limit: int = 20, 
        is_favorite: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        query = supabase_client.from_("exports").select("*").eq("user_id", user_id)
        if is_favorite is not None:
            query = query.eq("is_favorite", is_favorite)
        res = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        return res.data if res else []

    def log_audit(
        self, 
        user_id: Optional[str], 
        action: str, 
        export_id: Optional[str] = None, 
        ip_address: Optional[str] = None, 
        user_agent: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "action": action,
            "export_id": export_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        try:
            res = supabase_client.from_("export_audit_logs").insert(payload).execute()
            return res.data[0] if (res and res.data) else {}
        except Exception:
            return payload

export_repository = ExportRepository()
