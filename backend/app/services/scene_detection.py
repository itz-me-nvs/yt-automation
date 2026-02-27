"""
Scene detection service using PySceneDetect.

PySceneDetect analyzes video frames to detect scene boundaries using:
- ContentDetector: Detects changes in HSV color space (best for most videos)
- ThresholdDetector: Detects fade-in/fade-out transitions
- AdaptiveDetector: Adapts threshold based on surrounding frames

This helps identify natural cut points and distinct segments in the video.
"""
import os
import logging
import subprocess
import json
import tempfile

logger = logging.getLogger(__name__)


def detect_scenes(video_path: str, threshold: float = 27.0) -> list[dict]:
    """
    Detect scene boundaries in a video using PySceneDetect.

    Args:
        video_path: Path to the video file
        threshold: Content detection threshold (lower = more sensitive)

    Returns:
        List of scene dicts with start_time, end_time, duration
    """
    try:
        from scenedetect import open_video, SceneManager, ContentDetector

        video = open_video(video_path)
        scene_manager = SceneManager()

        # ContentDetector uses HSV color space analysis to find scene changes
        scene_manager.add_detector(ContentDetector(threshold=threshold))

        # Process the video
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()

        scenes = []
        for i, (start, end) in enumerate(scene_list):
            start_sec = start.get_seconds()
            end_sec = end.get_seconds()
            scenes.append({
                "index": i,
                "start_time": round(start_sec, 2),
                "end_time": round(end_sec, 2),
                "duration": round(end_sec - start_sec, 2),
                "description": f"Scene {i + 1}",
                "confidence": 1.0,
            })

        logger.info(f"Detected {len(scenes)} scenes in {video_path}")
        return scenes

    except ImportError:
        logger.warning("PySceneDetect not available, using FFmpeg fallback")
        return _ffmpeg_scene_detect(video_path, threshold)


def _ffmpeg_scene_detect(video_path: str, threshold: float = 0.3) -> list[dict]:
    """
    Fallback scene detection using FFmpeg's scene change filter.
    Uses the 'select' filter to detect significant frame changes.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "json", video_path,
            ],
            capture_output=True, text=True, timeout=30
        )
        duration = float(json.loads(result.stdout)["format"]["duration"])

        # Use FFmpeg scene detection filter
        result = subprocess.run(
            [
                "ffmpeg", "-i", video_path,
                "-vf", f"select='gt(scene,{threshold})',showinfo",
                "-f", "null", "-",
            ],
            capture_output=True, text=True, timeout=300
        )

        # Parse scene change timestamps from FFmpeg output
        scene_times = [0.0]
        for line in result.stderr.split("\n"):
            if "pts_time:" in line:
                try:
                    pts_str = line.split("pts_time:")[1].split()[0]
                    scene_times.append(float(pts_str))
                except (IndexError, ValueError):
                    continue

        scene_times.append(duration)
        scene_times = sorted(set(scene_times))

        scenes = []
        for i in range(len(scene_times) - 1):
            start = scene_times[i]
            end = scene_times[i + 1]
            if end - start >= 1.0:  # Minimum 1 second scene
                scenes.append({
                    "index": i,
                    "start_time": round(start, 2),
                    "end_time": round(end, 2),
                    "duration": round(end - start, 2),
                    "description": f"Scene {len(scenes) + 1}",
                    "confidence": 0.8,
                })

        return scenes

    except Exception as e:
        logger.error(f"FFmpeg scene detection failed: {e}")
        return []


def extract_scene_frames(video_path: str, scenes: list[dict], output_dir: str) -> list[str]:
    """
    Extract a representative frame from each scene for visual analysis.
    Takes a frame from the middle of each scene.
    """
    os.makedirs(output_dir, exist_ok=True)
    frame_paths = []

    for scene in scenes:
        mid_time = (scene["start_time"] + scene["end_time"]) / 2
        output_path = os.path.join(output_dir, f"scene_{scene['index']:04d}.jpg")

        try:
            subprocess.run(
                [
                    "ffmpeg", "-ss", str(mid_time),
                    "-i", video_path,
                    "-vframes", "1",
                    "-q:v", "2",
                    "-y", output_path,
                ],
                capture_output=True, text=True, timeout=30
            )
            if os.path.exists(output_path):
                frame_paths.append(output_path)
            else:
                frame_paths.append(None)
        except Exception as e:
            logger.warning(f"Failed to extract frame for scene {scene['index']}: {e}")
            frame_paths.append(None)

    return frame_paths
