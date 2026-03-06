from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VideoUploadResponse(BaseModel):
    id: str
    title: str
    status: str
    message: str


class YouTubeLinkRequest(BaseModel):
    url: str
    title: Optional[str] = None


class VideoResponse(BaseModel):
    id: str
    title: str
    source_type: str
    source_url: Optional[str]
    duration: Optional[float]
    resolution: Optional[str]
    file_size: Optional[int]
    thumbnail_path: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: str
    updated_at: str


class SceneInfo(BaseModel):
    start_time: float
    end_time: float
    duration: float
    description: str
    confidence: float


class HighlightInfo(BaseModel):
    start_time: float
    end_time: float
    duration: float
    category: str
    title: str
    description: str
    score: float
    reasons: list[str]


class EmotionSegment(BaseModel):
    start_time: float
    end_time: float
    emotion: str
    intensity: float
    text: str


class AudioEnergyPoint(BaseModel):
    time: float
    energy: float
    is_peak: bool


class AnalysisResponse(BaseModel):
    id: str
    video_id: str
    transcript: Optional[str]
    scenes: list[SceneInfo]
    highlights: list[HighlightInfo]
    emotions: list[EmotionSegment]
    categories: dict
    summary: Optional[str]
    audio_energy: list[AudioEnergyPoint]
    created_at: str


class ShortResponse(BaseModel):
    id: str
    video_id: str
    title: str
    description: Optional[str]
    start_time: float
    end_time: float
    duration: float
    category: Optional[str]
    score: float
    file_path: Optional[str]
    thumbnail_path: Optional[str]
    template_id: Optional[str] = None
    template_variables: Optional[dict] = None
    status: str
    created_at: str


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    preview_color: str
    variables: list[str]
    tags: list[str]


class TemplateSuggestion(BaseModel):
    template_id: str
    main_text: str
    sub_text: str
    confidence: float


class RegenerateShortRequest(BaseModel):
    video_id: str
    highlight_index: int
    template_id: str
    main_text: str
    sub_text: str = ""


class CustomTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    category: str
    base_template_id: str
    variables: dict[str, str]


class ChannelInfoResponse(BaseModel):
    id: str
    channel_name: Optional[str]
    channel_url: Optional[str]
    total_videos_processed: int
    total_shorts_generated: int
    settings: dict
    created_at: str
    updated_at: str


class ChannelSettingsUpdate(BaseModel):
    channel_name: Optional[str] = None
    channel_url: Optional[str] = None
    settings: Optional[dict] = None


class AnalysisProgress(BaseModel):
    video_id: str
    stage: str
    progress: float
    message: str
