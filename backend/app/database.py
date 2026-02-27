import aiosqlite
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "yt_automation.db")


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source_type TEXT NOT NULL CHECK(source_type IN ('upload', 'youtube')),
            source_url TEXT,
            file_path TEXT NOT NULL,
            duration REAL,
            resolution TEXT,
            file_size INTEGER,
            thumbnail_path TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending', 'downloading', 'analyzing', 'generating_shorts', 'completed', 'failed')),
            error_message TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS analysis_results (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
            transcript TEXT,
            scenes_json TEXT,
            highlights_json TEXT,
            emotions_json TEXT,
            categories_json TEXT,
            summary TEXT,
            audio_energy_json TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS shorts (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
            analysis_id TEXT REFERENCES analysis_results(id),
            title TEXT NOT NULL,
            description TEXT,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            duration REAL NOT NULL,
            category TEXT,
            score REAL DEFAULT 0.0,
            file_path TEXT,
            thumbnail_path TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending', 'generating', 'completed', 'failed')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS channel_info (
            id TEXT PRIMARY KEY,
            channel_name TEXT,
            channel_url TEXT,
            total_videos_processed INTEGER DEFAULT 0,
            total_shorts_generated INTEGER DEFAULT 0,
            settings_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # Insert default channel info if not exists
    cursor = await db.execute("SELECT COUNT(*) FROM channel_info")
    count = (await cursor.fetchone())[0]
    if count == 0:
        await db.execute(
            "INSERT INTO channel_info (id, channel_name, settings_json) VALUES (?, ?, ?)",
            ("default", "My YouTube Channel", json.dumps({
                "default_short_duration": 60,
                "min_highlight_score": 0.5,
                "preferred_categories": ["funny", "highlights", "emotional", "music"],
                "auto_generate_shorts": True,
            }))
        )

    await db.commit()
    await db.close()
