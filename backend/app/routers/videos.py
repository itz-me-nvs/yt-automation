"""
Video management API routes.
Handles video upload, YouTube link download, listing, and status.
"""
import os
import uuid
import json
import shutil
import asyncio
import logging
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException

from ..database import get_db
from ..models.schemas import VideoUploadResponse, YouTubeLinkRequest, VideoResponse
from ..services.video_downloader import download_video, get_video_resolution, get_video_duration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["videos"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(None),
    background_tasks: BackgroundTasks = None,
):
    """Upload a video file for analysis."""
    video_id = str(uuid.uuid4())
    video_title = title or file.filename or "Untitled"

    # Save uploaded file
    video_dir = os.path.join(UPLOAD_DIR, video_id)
    os.makedirs(video_dir, exist_ok=True)
    file_path = os.path.join(video_dir, file.filename or "video.mp4")

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    file_size = os.path.getsize(file_path)
    duration = get_video_duration(file_path)
    resolution = get_video_resolution(file_path)

    # Save to database
    db = await get_db()
    await db.execute(
        """INSERT INTO videos (id, title, source_type, file_path, duration, resolution, file_size, status)
           VALUES (?, ?, 'upload', ?, ?, ?, ?, 'pending')""",
        (video_id, video_title, file_path, duration, resolution, file_size),
    )
    await db.commit()
    await db.close()

    return VideoUploadResponse(
        id=video_id,
        title=video_title,
        status="pending",
        message=f"Video uploaded successfully. Size: {file_size / 1024 / 1024:.1f}MB",
    )


@router.post("/youtube", response_model=VideoUploadResponse)
async def add_youtube_video(
    request: YouTubeLinkRequest,
    background_tasks: BackgroundTasks,
):
    """Add a YouTube video by URL for download and analysis."""
    video_id = str(uuid.uuid4())

    # Save initial record
    db = await get_db()
    await db.execute(
        """INSERT INTO videos (id, title, source_type, source_url, file_path, status)
           VALUES (?, ?, 'youtube', ?, '', 'downloading')""",
        (video_id, request.title or "Downloading...", request.url),
    )
    await db.commit()
    await db.close()

    # Start download in background
    background_tasks.add_task(_download_youtube, video_id, request.url)

    return VideoUploadResponse(
        id=video_id,
        title=request.title or "Downloading...",
        status="downloading",
        message="YouTube video download started",
    )


async def _download_youtube(video_id: str, url: str):
    """Background task to download a YouTube video."""
    db = await get_db()
    try:
        result = await asyncio.to_thread(download_video, url, video_id)

        await db.execute(
            """UPDATE videos SET
                title = ?, file_path = ?, duration = ?, resolution = ?,
                file_size = ?, thumbnail_path = ?, status = 'pending',
                updated_at = datetime('now')
               WHERE id = ?""",
            (
                result["title"], result["file_path"], result["duration"],
                result["resolution"], result["file_size"],
                result.get("thumbnail_path"), video_id,
            ),
        )
        await db.commit()
        logger.info(f"YouTube video {video_id} downloaded successfully")

    except Exception as e:
        logger.error(f"YouTube download failed for {video_id}: {e}")
        await db.execute(
            """UPDATE videos SET status = 'failed', error_message = ?,
               updated_at = datetime('now') WHERE id = ?""",
            (str(e)[:500], video_id),
        )
        await db.commit()
    finally:
        await db.close()


@router.get("/", response_model=list[VideoResponse])
async def list_videos():
    """List all videos."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM videos ORDER BY created_at DESC"
    )
    rows = await cursor.fetchall()
    await db.close()

    videos = []
    for row in rows:
        videos.append(VideoResponse(
            id=row["id"],
            title=row["title"],
            source_type=row["source_type"],
            source_url=row["source_url"],
            duration=row["duration"],
            resolution=row["resolution"],
            file_size=row["file_size"],
            thumbnail_path=row["thumbnail_path"],
            status=row["status"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        ))

    return videos


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str):
    """Get video details by ID."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
    row = await cursor.fetchone()
    await db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Video not found")

    return VideoResponse(
        id=row["id"],
        title=row["title"],
        source_type=row["source_type"],
        source_url=row["source_url"],
        duration=row["duration"],
        resolution=row["resolution"],
        file_size=row["file_size"],
        thumbnail_path=row["thumbnail_path"],
        status=row["status"],
        error_message=row["error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """Delete a video and its associated data."""
    db = await get_db()
    cursor = await db.execute("SELECT file_path FROM videos WHERE id = ?", (video_id,))
    row = await cursor.fetchone()

    if not row:
        await db.close()
        raise HTTPException(status_code=404, detail="Video not found")

    # Delete file from disk
    video_dir = os.path.join(UPLOAD_DIR, video_id)
    if os.path.exists(video_dir):
        shutil.rmtree(video_dir, ignore_errors=True)

    # Delete from database (cascades to analysis and shorts)
    await db.execute("DELETE FROM shorts WHERE video_id = ?", (video_id,))
    await db.execute("DELETE FROM analysis_results WHERE video_id = ?", (video_id,))
    await db.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    await db.commit()
    await db.close()

    return {"message": "Video deleted successfully"}
