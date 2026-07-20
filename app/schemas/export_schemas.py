from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ExportCustomSettings(BaseModel):
    accent_color: Optional[str] = "#3b82f6"
    background_type: Optional[str] = "color" # 'color', 'gradient', 'photo', 'transparent'
    background_value: Optional[str] = "#090d16" # hex, gradient string, or image URL
    logo_url: Optional[str] = None
    avatar_url: Optional[str] = None
    corner_radius: Optional[int] = 16
    glass_opacity: Optional[float] = 0.2
    text_color: Optional[str] = "#ffffff"
    metric_order: Optional[List[str]] = None
    units: Optional[str] = "metric" # 'metric' or 'imperial'
    language: Optional[str] = "en"
    aspect_ratio: Optional[str] = "square" # 'story', 'post', 'square', 'landscape', 'wallpaper'
    show_logo: Optional[bool] = True
    custom_title: Optional[str] = None

class ExportCreateRequest(BaseModel):
    metric_type: str = Field(..., description="Metric tab to export: health, nutrition, workouts, sleep, body, achievements, year_in_review, custom")
    date_range: str = Field(..., description="today, yesterday, last_7_days, last_30_days, this_month, last_month, this_year, custom")
    custom_start: Optional[str] = None
    custom_end: Optional[str] = None
    layout_type: str = Field(..., description="minimal, glass, rings, strava, whoop, oura, garmin, nutrition, transformation, sleep, heart_health, hydration, weekly_summary, monthly_report, year_in_review, achievement, ai_insights, medical_report, coach_report, complete_dashboard")
    output_format: str = Field(..., description="png, jpeg, pdf, csv, excel, json, zip")
    theme: str = Field(..., description="light, dark, glass, transparent, gradient, blue, green, black, dynamic")
    custom_settings: Optional[ExportCustomSettings] = Field(default_factory=ExportCustomSettings)

class ExportShareRequest(BaseModel):
    platform: str = Field(..., description="instagram_story, instagram_feed, whatsapp, facebook, twitter, linkedin, telegram, email")
    custom_message: Optional[str] = None

class ExportResponse(BaseModel):
    id: str
    user_id: str
    metric_type: str
    date_range: str
    custom_start: Optional[str]
    custom_end: Optional[str]
    layout_type: str
    output_format: str
    theme: str
    custom_settings: Dict[str, Any]
    status: str
    file_url: Optional[str]
    shared_url: Optional[str]
    is_favorite: bool
    error_message: Optional[str]
    created_at: str
