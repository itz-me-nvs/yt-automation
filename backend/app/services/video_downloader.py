"""
YouTube video downloader service using yt-dlp.
Downloads videos from YouTube URLs for local processing.
"""
import os
import uuid
import subprocess
import json
import logging

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_video_info(url: str) -> dict:
    """Extract video metadata from a YouTube URL using yt-dlp."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp error: {result.stderr}")
        return json.loads(result.stdout)
    except FileNotFoundError:
        raise RuntimeError("yt-dlp is not installed. Install with: pip install yt-dlp")


def download_video(url: str, video_id: str) -> dict:
    """
    Download a video from YouTube using yt-dlp.
    Returns dict with file_path, title, duration, resolution, file_size.
    """
    output_dir = os.path.join(UPLOAD_DIR, video_id)
    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    try:
        # First get info
        info = get_video_info(url)
        title = info.get("title", "Untitled")
        duration = info.get("duration", 0)

        # Download with best quality up to 1080p
        result = subprocess.run(
            [
                "yt-dlp",
                "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "--merge-output-format", "mp4",
                "-o", output_template,
                "--write-thumbnail",
                "--convert-thumbnails", "jpg",
                url,
            ],
            capture_output=True, text=True, timeout=600
        )

        if result.returncode != 0:
            raise RuntimeError(f"Download failed: {result.stderr}")

        # Find the downloaded file
        video_file = None
        thumbnail_file = None
        for f in os.listdir(output_dir):
            if f.endswith(".mp4"):
                video_file = os.path.join(output_dir, f)
            elif f.endswith(".jpg") or f.endswith(".webp") or f.endswith(".png"):
                thumbnail_file = os.path.join(output_dir, f)

        if not video_file:
            raise RuntimeError("Downloaded file not found")

        file_size = os.path.getsize(video_file)

        # Get resolution from ffprobe
        resolution = get_video_resolution(video_file)

        return {
            "file_path": video_file,
            "title": title,
            "duration": duration,
            "resolution": resolution,
            "file_size": file_size,
            "thumbnail_path": thumbnail_file,
        }

    except subprocess.TimeoutExpired:
        raise RuntimeError("Download timed out after 10 minutes")


def get_video_resolution(file_path: str) -> str:
    """Get video resolution using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "json",
                file_path,
            ],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            streams = data.get("streams", [])
            if streams:
                w = streams[0].get("width", 0)
                h = streams[0].get("height", 0)
                return f"{w}x{h}"
    except Exception as e:
        logger.warning(f"Could not get resolution: {e}")
    return "unknown"


def get_video_duration(file_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                file_path,
            ],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return float(data.get("format", {}).get("duration", 0))
    except Exception as e:
        logger.warning(f"Could not get duration: {e}")
    return 0.0
