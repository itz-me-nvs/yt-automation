"""
Analysis API routes.
Handles starting analysis, checking progress, and retrieving results.
"""
import uuid
import json
import asyncio
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..database import get_db
from ..models.schemas import AnalysisResponse, ShortResponse
from ..services.analysis_pipeline import run_analysis_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# In-memory progress tracking (per-video)
_progress: dict[str, dict] = {}


@router.post("/{video_id}/start")
async def start_analysis(video_id: str, background_tasks: BackgroundTasks):
    """Start the ML analysis pipeline for a video."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
    video = await cursor.fetchone()

    if not video:
        await db.close()
        raise HTTPException(status_code=404, detail="Video not found")

    if video["status"] in ("analyzing", "generating_shorts"):
        await db.close()
        raise HTTPException(status_code=409, detail="Analysis already in progress")

    if not video["file_path"] or video["status"] == "downloading":
        await db.close()
        raise HTTPException(status_code=400, detail="Video not ready for analysis")

    # Update status
    await db.execute(
        "UPDATE videos SET status = 'analyzing', updated_at = datetime('now') WHERE id = ?",
        (video_id,),
    )
    await db.commit()
    await db.close()

    # Initialize progress
    _progress[video_id] = {
        "stage": "starting",
        "progress": 0.0,
        "message": "Starting analysis pipeline...",
    }

    # Run pipeline in background
    background_tasks.add_task(
        _run_analysis_background,
        video_id,
        video["file_path"],
    )

    return {
        "message": "Analysis started",
        "video_id": video_id,
    }


@router.get("/{video_id}/progress")
async def get_analysis_progress(video_id: str):
    """Get current analysis progress for a video."""
    if video_id in _progress:
        return _progress[video_id]

    # Check if analysis is already complete
    db = await get_db()
    cursor = await db.execute(
        "SELECT status FROM videos WHERE id = ?", (video_id,)
    )
    video = await cursor.fetchone()
    await db.close()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video["status"] == "completed":
        return {"stage": "completed", "progress": 1.0, "message": "Analysis complete"}

    return {"stage": "unknown", "progress": 0.0, "message": "No analysis in progress"}


@router.get("/{video_id}/results")
async def get_analysis_results(video_id: str):
    """Get analysis results for a video."""
    db = await get_db()

    # Get analysis results
    cursor = await db.execute(
        "SELECT * FROM analysis_results WHERE video_id = ? ORDER BY created_at DESC LIMIT 1",
        (video_id,),
    )
    analysis = await cursor.fetchone()

    if not analysis:
        await db.close()
        raise HTTPException(status_code=404, detail="No analysis results found")

    # Get shorts
    cursor = await db.execute(
        "SELECT * FROM shorts WHERE video_id = ? ORDER BY score DESC",
        (video_id,),
    )
    shorts_rows = await cursor.fetchall()
    await db.close()

    shorts = []
    for row in shorts_rows:
        shorts.append(ShortResponse(
            id=row["id"],
            video_id=row["video_id"],
            title=row["title"],
            description=row["description"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            duration=row["duration"],
            category=row["category"],
            score=row["score"] or 0,
            file_path=row["file_path"],
            thumbnail_path=row["thumbnail_path"],
            status=row["status"],
            created_at=row["created_at"],
        ))

    return {
        "analysis": AnalysisResponse(
            id=analysis["id"],
            video_id=analysis["video_id"],
            transcript=analysis["transcript"],
            scenes=json.loads(analysis["scenes_json"] or "[]"),
            highlights=json.loads(analysis["highlights_json"] or "[]"),
            emotions=json.loads(analysis["emotions_json"] or "[]"),
            categories=json.loads(analysis["categories_json"] or "{}"),
            summary=analysis["summary"],
            audio_energy=json.loads(analysis["audio_energy_json"] or "[]"),
            created_at=analysis["created_at"],
        ),
        "shorts": shorts,
    }


@router.get("/{video_id}/shorts", response_model=list[ShortResponse])
async def get_shorts(video_id: str):
    """Get generated shorts for a video."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM shorts WHERE video_id = ? ORDER BY score DESC",
        (video_id,),
    )
    rows = await cursor.fetchall()
    await db.close()

    return [
        ShortResponse(
            id=row["id"],
            video_id=row["video_id"],
            title=row["title"],
            description=row["description"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            duration=row["duration"],
            category=row["category"],
            score=row["score"] or 0,
            file_path=row["file_path"],
            thumbnail_path=row["thumbnail_path"],
            status=row["status"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


async def _progress_callback(
    video_id: str, stage: str, progress: float, message: str,
):
    """Update progress tracking for the analysis pipeline."""
    _progress[video_id] = {
        "stage": stage,
        "progress": progress,
        "message": message,
    }


async def _run_analysis_background(video_id: str, video_path: str):
    """Run the full analysis pipeline in the background."""
    db = await get_db()
    try:
        results = await run_analysis_pipeline(
            video_path=video_path,
            video_id=video_id,
            progress_callback=_progress_callback,
        )

        # Save analysis results
        analysis_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO analysis_results
               (id, video_id, transcript, scenes_json, highlights_json,
                emotions_json, categories_json, summary, audio_energy_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                analysis_id,
                video_id,
                results.get("transcript", ""),
                json.dumps(results.get("scenes", [])),
                json.dumps(results.get("highlights", [])),
                json.dumps(results.get("emotions", [])),
                json.dumps(results.get("categories", {})),
                results.get("summary", ""),
                json.dumps(results.get("audio_energy", [])),
            ),
        )

        # Save generated shorts
        for short_data in results.get("shorts", []):
            if short_data.get("status") == "completed":
                highlight = short_data.get("highlight", {})
                await db.execute(
                    """INSERT INTO shorts
                       (id, video_id, analysis_id, title, description,
                        start_time, end_time, duration, category, score,
                        file_path, thumbnail_path, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed')""",
                    (
                        short_data["short_id"],
                        video_id,
                        analysis_id,
                        highlight.get("title", "Short"),
                        highlight.get("description", ""),
                        highlight.get("start_time", 0),
                        highlight.get("end_time", 0),
                        short_data.get("duration", 0),
                        highlight.get("category", "general"),
                        highlight.get("score", 0),
                        short_data.get("file_path", ""),
                        short_data.get("thumbnail_path"),
                    ),
                )

        # Update video status
        await db.execute(
            "UPDATE videos SET status = 'completed', updated_at = datetime('now') WHERE id = ?",
            (video_id,),
        )
        await db.commit()

        # Update channel stats
        await db.execute(
            """UPDATE channel_info SET
                total_videos_processed = total_videos_processed + 1,
                total_shorts_generated = total_shorts_generated + ?,
                updated_at = datetime('now')
               WHERE id = 'default'""",
            (len([s for s in results.get("shorts", []) if s.get("status") == "completed"]),),
        )
        await db.commit()

        _progress[video_id] = {
            "stage": "completed",
            "progress": 1.0,
            "message": "Analysis complete!",
        }

    except Exception as e:
        logger.error(f"Analysis failed for {video_id}: {e}", exc_info=True)
        await db.execute(
            """UPDATE videos SET status = 'failed', error_message = ?,
               updated_at = datetime('now') WHERE id = ?""",
            (str(e)[:500], video_id),
        )
        await db.commit()

        _progress[video_id] = {
            "stage": "error",
            "progress": 0.0,
            "message": f"Analysis failed: {str(e)[:200]}",
        }

    finally:
        await db.close()
