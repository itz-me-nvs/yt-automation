"""
Channel/Account management API routes.
"""
import json
from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..models.schemas import ChannelInfoResponse, ChannelSettingsUpdate

router = APIRouter(prefix="/api/channel", tags=["channel"])


@router.get("/", response_model=ChannelInfoResponse)
async def get_channel_info():
    """Get channel information and settings."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM channel_info WHERE id = 'default'")
    row = await cursor.fetchone()
    await db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Channel info not found")

    return ChannelInfoResponse(
        id=row["id"],
        channel_name=row["channel_name"],
        channel_url=row["channel_url"],
        total_videos_processed=row["total_videos_processed"],
        total_shorts_generated=row["total_shorts_generated"],
        settings=json.loads(row["settings_json"] or "{}"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.put("/", response_model=ChannelInfoResponse)
async def update_channel_info(update: ChannelSettingsUpdate):
    """Update channel information and settings."""
    db = await get_db()

    # Get current data
    cursor = await db.execute("SELECT * FROM channel_info WHERE id = 'default'")
    row = await cursor.fetchone()
    if not row:
        await db.close()
        raise HTTPException(status_code=404, detail="Channel info not found")

    # Merge updates
    current_settings = json.loads(row["settings_json"] or "{}")
    if update.settings:
        current_settings.update(update.settings)

    channel_name = update.channel_name or row["channel_name"]
    channel_url = update.channel_url or row["channel_url"]

    await db.execute(
        """UPDATE channel_info SET
            channel_name = ?, channel_url = ?, settings_json = ?,
            updated_at = datetime('now')
           WHERE id = 'default'""",
        (channel_name, channel_url, json.dumps(current_settings)),
    )
    await db.commit()

    # Fetch updated
    cursor = await db.execute("SELECT * FROM channel_info WHERE id = 'default'")
    row = await cursor.fetchone()
    await db.close()

    return ChannelInfoResponse(
        id=row["id"],
        channel_name=row["channel_name"],
        channel_url=row["channel_url"],
        total_videos_processed=row["total_videos_processed"],
        total_shorts_generated=row["total_shorts_generated"],
        settings=json.loads(row["settings_json"] or "{}"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/stats")
async def get_channel_stats():
    """Get channel statistics and dashboard data."""
    db = await get_db()

    # Get channel info
    cursor = await db.execute("SELECT * FROM channel_info WHERE id = 'default'")
    channel = await cursor.fetchone()

    # Get video counts by status
    cursor = await db.execute(
        "SELECT status, COUNT(*) as count FROM videos GROUP BY status"
    )
    status_counts = {row["status"]: row["count"] for row in await cursor.fetchall()}

    # Get shorts counts by category
    cursor = await db.execute(
        "SELECT category, COUNT(*) as count FROM shorts WHERE status = 'completed' GROUP BY category"
    )
    category_counts = {row["category"]: row["count"] for row in await cursor.fetchall()}

    # Recent videos
    cursor = await db.execute(
        "SELECT id, title, status, created_at FROM videos ORDER BY created_at DESC LIMIT 5"
    )
    recent_videos = [dict(row) for row in await cursor.fetchall()]

    # Recent shorts
    cursor = await db.execute(
        """SELECT s.id, s.title, s.category, s.score, s.duration, s.status, s.created_at,
                  v.title as video_title
           FROM shorts s JOIN videos v ON s.video_id = v.id
           ORDER BY s.created_at DESC LIMIT 10"""
    )
    recent_shorts = [dict(row) for row in await cursor.fetchall()]

    # Total durations
    cursor = await db.execute(
        "SELECT COALESCE(SUM(duration), 0) as total FROM videos WHERE status = 'completed'"
    )
    total_video_duration = (await cursor.fetchone())["total"]

    cursor = await db.execute(
        "SELECT COALESCE(SUM(duration), 0) as total FROM shorts WHERE status = 'completed'"
    )
    total_shorts_duration = (await cursor.fetchone())["total"]

    await db.close()

    return {
        "channel": {
            "name": channel["channel_name"] if channel else "My Channel",
            "total_videos": channel["total_videos_processed"] if channel else 0,
            "total_shorts": channel["total_shorts_generated"] if channel else 0,
        },
        "video_status_counts": status_counts,
        "category_counts": category_counts,
        "recent_videos": recent_videos,
        "recent_shorts": recent_shorts,
        "total_video_duration": total_video_duration,
        "total_shorts_duration": total_shorts_duration,
    }
