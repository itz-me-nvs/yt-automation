"""
YouTube Shorts generator service.

Takes identified highlights and generates vertical (9:16) short videos
using FFmpeg. Handles:
- Cropping/padding to 9:16 aspect ratio (1080x1920)
- Trimming to highlight timestamps
- Generating thumbnails for each short
- Adding fade in/out transitions
"""
import os
import subprocess
import logging
import uuid

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# YouTube Shorts specs
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920
MAX_DURATION = 60  # seconds


def generate_short(
    video_path: str,
    start_time: float,
    end_time: float,
    short_id: str,
    title: str = "Short",
    add_fade: bool = True,
) -> dict:
    """
    Generate a YouTube Short from a segment of the source video.

    Process:
    1. Trim video to start_time/end_time
    2. Convert to 9:16 vertical format (center crop or pad)
    3. Re-encode with optimal settings for YouTube Shorts
    4. Generate thumbnail

    Args:
        video_path: Path to source video
        start_time: Start timestamp in seconds
        end_time: End timestamp in seconds
        short_id: Unique ID for this short
        title: Title for filename
        add_fade: Whether to add fade in/out

    Returns:
        dict with file_path, thumbnail_path, duration
    """
    duration = min(end_time - start_time, MAX_DURATION)
    output_subdir = os.path.join(OUTPUT_DIR, short_id)
    os.makedirs(output_subdir, exist_ok=True)

    safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[:50].strip()
    output_path = os.path.join(output_subdir, f"{safe_title}.mp4")
    thumbnail_path = os.path.join(output_subdir, "thumbnail.jpg")

    # Get source video dimensions
    src_width, src_height = _get_dimensions(video_path)

    # Build FFmpeg filter for 9:16 conversion
    vf_filters = _build_vertical_filter(src_width, src_height, add_fade, duration)

    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-ss", str(start_time),
        "-i", video_path,
        "-t", str(duration),
        "-vf", vf_filters,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-movflags", "+faststart",
        "-y",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"Short generation failed: {result.stderr[:200]}")

        # Generate thumbnail from middle of clip
        thumb_time = duration / 2
        _generate_thumbnail(video_path, start_time + thumb_time, thumbnail_path)

        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

        return {
            "file_path": output_path,
            "thumbnail_path": thumbnail_path if os.path.exists(thumbnail_path) else None,
            "duration": duration,
            "file_size": file_size,
        }

    except subprocess.TimeoutExpired:
        raise RuntimeError("Short generation timed out")


def _get_dimensions(video_path: str) -> tuple[int, int]:
    """Get video dimensions using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0:s=x",
                video_path,
            ],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and "x" in result.stdout:
            parts = result.stdout.strip().split("x")
            return int(parts[0]), int(parts[1])
    except Exception as e:
        logger.warning(f"Could not get dimensions: {e}")
    return 1920, 1080  # Default to landscape HD


def _build_vertical_filter(
    src_width: int,
    src_height: int,
    add_fade: bool,
    duration: float,
) -> str:
    """
    Build FFmpeg video filter chain for 9:16 conversion.

    Strategy:
    - If source is landscape (16:9): center crop to 9:16
    - If source is portrait: scale to fit 9:16
    - If source is square: pad to 9:16
    """
    target_ratio = SHORTS_WIDTH / SHORTS_HEIGHT  # 0.5625
    src_ratio = src_width / src_height if src_height > 0 else 1.78

    filters = []

    if src_ratio > target_ratio:
        # Source is wider than target (landscape -> portrait)
        # Crop width from center, then scale
        crop_width = int(src_height * target_ratio)
        crop_x = (src_width - crop_width) // 2
        filters.append(f"crop={crop_width}:{src_height}:{crop_x}:0")
        filters.append(f"scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}")
    elif src_ratio < target_ratio:
        # Source is taller or square
        # Scale width to match, pad height
        new_width = SHORTS_WIDTH
        new_height = int(new_width / src_ratio)
        if new_height < SHORTS_HEIGHT:
            filters.append(f"scale={new_width}:{new_height}")
            pad_y = (SHORTS_HEIGHT - new_height) // 2
            filters.append(f"pad={SHORTS_WIDTH}:{SHORTS_HEIGHT}:0:{pad_y}:black")
        else:
            # Crop height
            crop_height = int(src_width / target_ratio)
            crop_y = (src_height - crop_height) // 2
            filters.append(f"crop={src_width}:{crop_height}:0:{max(0, crop_y)}")
            filters.append(f"scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}")
    else:
        # Same ratio, just scale
        filters.append(f"scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}")

    # Add fade effects
    if add_fade and duration > 2:
        fade_duration = 0.5
        filters.append(f"fade=t=in:st=0:d={fade_duration}")
        filters.append(f"fade=t=out:st={duration - fade_duration}:d={fade_duration}")

    return ",".join(filters)


def _generate_thumbnail(video_path: str, timestamp: float, output_path: str):
    """Generate a thumbnail at the given timestamp."""
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-vf", f"scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}:force_original_aspect_ratio=decrease,"
                       f"pad={SHORTS_WIDTH}:{SHORTS_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
                "-q:v", "2",
                "-y", output_path,
            ],
            capture_output=True, text=True, timeout=30
        )
    except Exception as e:
        logger.warning(f"Thumbnail generation failed: {e}")


def batch_generate_shorts(
    video_path: str,
    highlights: list[dict],
    max_shorts: int = 10,
) -> list[dict]:
    """
    Generate multiple shorts from a list of highlights.

    Args:
        video_path: Source video path
        highlights: List of highlight dicts with start_time, end_time, title, etc.
        max_shorts: Maximum number of shorts to generate

    Returns:
        List of generation result dicts
    """
    # Sort by score descending, take top N
    sorted_highlights = sorted(highlights, key=lambda x: x.get("score", 0), reverse=True)
    selected = sorted_highlights[:max_shorts]

    results = []
    for highlight in selected:
        short_id = str(uuid.uuid4())
        try:
            result = generate_short(
                video_path=video_path,
                start_time=highlight["start_time"],
                end_time=highlight["end_time"],
                short_id=short_id,
                title=highlight.get("title", "Short"),
            )
            result["highlight"] = highlight
            result["short_id"] = short_id
            result["status"] = "completed"
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to generate short: {e}")
            results.append({
                "short_id": short_id,
                "highlight": highlight,
                "status": "failed",
                "error": str(e),
            })

    return results
