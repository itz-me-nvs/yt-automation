"""
Main analysis pipeline that orchestrates all ML services.

Pipeline stages:
1. Audio extraction & transcription (Whisper)
2. Scene detection (PySceneDetect / FFmpeg)
3. Audio energy analysis (librosa)
4. Frame extraction & visual analysis (CLIP)
5. Content analysis with LLM (Ollama)
6. Highlight merging & scoring
7. Short video generation (FFmpeg)

Each stage reports progress via a callback function.
"""
import os
import json
import uuid
import logging
import tempfile
from typing import Callable, Optional

from .transcription import transcribe_audio
from .scene_detection import detect_scenes, extract_scene_frames
from .audio_analysis import analyze_audio_energy
from .content_analyzer import analyze_transcript_with_llm, analyze_frames_with_clip
from .shorts_generator import batch_generate_shorts

logger = logging.getLogger(__name__)


async def run_analysis_pipeline(
    video_path: str,
    video_id: str,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """
    Run the full analysis pipeline on a video.

    Args:
        video_path: Path to the video file
        video_id: Unique video ID
        progress_callback: Optional callback(stage, progress, message)

    Returns:
        dict with all analysis results
    """
    results = {
        "video_id": video_id,
        "transcript": None,
        "segments": [],
        "scenes": [],
        "highlights": [],
        "emotions": [],
        "categories": {},
        "summary": None,
        "audio_energy": [],
        "shorts": [],
    }

    async def report(stage: str, progress: float, message: str):
        if progress_callback:
            await progress_callback(video_id, stage, progress, message)
        logger.info(f"[{video_id}] {stage}: {message} ({progress:.0%})")

    try:
        # ── Stage 1: Transcription with Whisper ─────────────────────────
        await report("transcription", 0.0, "Starting audio transcription with Whisper...")

        transcript_result = transcribe_audio(video_path)
        results["transcript"] = transcript_result.get("text", "")
        results["segments"] = transcript_result.get("segments", [])

        await report("transcription", 1.0,
                      f"Transcription complete. {len(results['segments'])} segments found. "
                      f"Language: {transcript_result.get('language', 'unknown')}")

        # ── Stage 2: Scene Detection ────────────────────────────────────
        await report("scene_detection", 0.0, "Detecting scenes using content analysis...")

        scenes = detect_scenes(video_path)
        results["scenes"] = scenes

        await report("scene_detection", 1.0,
                      f"Detected {len(scenes)} scenes")

        # ── Stage 3: Audio Energy Analysis ──────────────────────────────
        await report("audio_analysis", 0.0, "Analyzing audio energy levels with librosa...")

        audio_results = analyze_audio_energy(video_path)
        results["audio_energy"] = audio_results.get("energy_timeline", [])

        energy_peaks = audio_results.get("peaks", [])
        music_segments = audio_results.get("music_segments", [])

        await report("audio_analysis", 1.0,
                      f"Audio analysis complete. {len(energy_peaks)} energy peaks, "
                      f"{len(music_segments)} music segments found")

        # ── Stage 4: Visual Analysis with CLIP ──────────────────────────
        await report("visual_analysis", 0.0, "Extracting frames for visual analysis...")

        frames_dir = tempfile.mkdtemp(prefix=f"frames_{video_id}_")
        frame_paths = extract_scene_frames(video_path, scenes[:50], frames_dir)

        await report("visual_analysis", 0.3, f"Analyzing {len(frame_paths)} frames with CLIP...")

        frame_analysis = await analyze_frames_with_clip(
            [fp for fp in frame_paths if fp is not None]
        )

        # Enrich scenes with visual analysis
        for i, scene in enumerate(scenes):
            if i < len(frame_analysis):
                scene["visual_category"] = frame_analysis[i].get("primary", "unknown")
                scene["visual_scores"] = frame_analysis[i].get("categories", {})

        await report("visual_analysis", 1.0,
                      f"Visual analysis complete for {len(frame_analysis)} frames")

        # ── Stage 5: LLM Content Analysis ───────────────────────────────
        await report("content_analysis", 0.0, "Analyzing content with local LLM (Ollama)...")

        llm_results = await analyze_transcript_with_llm(
            transcript=results["transcript"],
            segments=results["segments"],
            video_duration=audio_results.get("duration", 0),
        )

        results["highlights"] = llm_results.get("highlights", [])
        results["emotions"] = llm_results.get("emotions", [])
        results["categories"] = llm_results.get("categories", {})
        results["summary"] = llm_results.get("summary", "")

        await report("content_analysis", 1.0,
                      f"LLM analysis complete. {len(results['highlights'])} highlights identified")

        # ── Stage 6: Merge & Score Highlights ───────────────────────────
        await report("scoring", 0.0, "Merging and scoring all highlights...")

        results["highlights"] = _merge_highlights(
            llm_highlights=results["highlights"],
            energy_peaks=energy_peaks,
            music_segments=music_segments,
            scenes=scenes,
        )

        # Sort by score
        results["highlights"].sort(key=lambda x: x.get("score", 0), reverse=True)

        await report("scoring", 1.0,
                      f"Final scoring complete. {len(results['highlights'])} highlights ranked")

        # ── Stage 7: Generate Shorts ────────────────────────────────────
        if results["highlights"]:
            await report("generation", 0.0,
                          f"Generating shorts from top {min(5, len(results['highlights']))} highlights...")

            shorts = batch_generate_shorts(
                video_path=video_path,
                highlights=results["highlights"],
                max_shorts=5,
            )
            results["shorts"] = shorts

            completed = sum(1 for s in shorts if s.get("status") == "completed")
            await report("generation", 1.0,
                          f"Generated {completed}/{len(shorts)} shorts successfully")
        else:
            await report("generation", 1.0, "No highlights found, skipping short generation")

        # Cleanup temp frames
        try:
            import shutil
            shutil.rmtree(frames_dir, ignore_errors=True)
        except Exception:
            pass

        return results

    except Exception as e:
        logger.error(f"Pipeline failed for video {video_id}: {e}", exc_info=True)
        await report("error", 0.0, f"Analysis failed: {str(e)}")
        raise


def _merge_highlights(
    llm_highlights: list[dict],
    energy_peaks: list[dict],
    music_segments: list[dict],
    scenes: list[dict],
) -> list[dict]:
    """
    Merge highlights from different sources (LLM, audio energy, visual)
    and compute final scores.

    Scoring weights:
    - LLM analysis: 0.4 (content understanding)
    - Audio energy: 0.3 (excitement level)
    - Visual analysis: 0.2 (visual interest)
    - Duration bonus: 0.1 (15-45 seconds ideal for Shorts)
    """
    merged = []

    # Add LLM highlights
    for h in llm_highlights:
        h["source"] = "llm"
        merged.append(h)

    # Add audio energy peaks as highlights if they don't overlap with existing
    for peak in energy_peaks:
        if not _overlaps_any(peak, merged, threshold=0.5):
            merged.append({
                "start_time": peak["start_time"],
                "end_time": peak["end_time"],
                "duration": peak["duration"],
                "category": "exciting",
                "title": "High Energy Moment",
                "description": f"Peak audio energy: {peak.get('max_energy', 0):.2f}",
                "score": peak.get("max_energy", 0.5) * 0.7,
                "reasons": ["High audio energy detected"],
                "source": "audio",
            })

    # Add music segments as potential highlights
    for seg in music_segments:
        if seg["duration"] >= 10 and not _overlaps_any(seg, merged, threshold=0.5):
            # Trim to max 60s
            end = min(seg["end_time"], seg["start_time"] + 60)
            merged.append({
                "start_time": seg["start_time"],
                "end_time": end,
                "duration": end - seg["start_time"],
                "category": "music",
                "title": "Music Moment",
                "description": "Detected music segment",
                "score": 0.5,
                "reasons": ["Music segment detected"],
                "source": "audio",
            })

    # Boost scores based on multi-source agreement
    for h in merged:
        base_score = h.get("score", 0.5)

        # Boost if near audio peak
        near_peak = any(
            _time_overlap(h, p) > 0.3
            for p in energy_peaks
        )
        if near_peak:
            base_score *= 1.2

        # Duration bonus (15-45 seconds is ideal)
        duration = h.get("duration", 0)
        if 15 <= duration <= 45:
            base_score *= 1.1
        elif duration > 60:
            base_score *= 0.8
        elif duration < 10:
            base_score *= 0.7

        # Ensure valid range
        h["score"] = round(min(1.0, max(0.0, base_score)), 4)

        # Ensure valid duration for Shorts (15-60 seconds)
        if h["duration"] < 15:
            # Extend to 15 seconds
            center = (h["start_time"] + h["end_time"]) / 2
            h["start_time"] = max(0, center - 7.5)
            h["end_time"] = h["start_time"] + 15
            h["duration"] = 15
        elif h["duration"] > 60:
            h["end_time"] = h["start_time"] + 60
            h["duration"] = 60

    return merged


def _overlaps_any(segment: dict, highlights: list[dict], threshold: float = 0.5) -> bool:
    """Check if a segment overlaps with any existing highlight."""
    for h in highlights:
        if _time_overlap(segment, h) > threshold:
            return True
    return False


def _time_overlap(a: dict, b: dict) -> float:
    """Calculate overlap ratio between two time segments."""
    start = max(a["start_time"], b["start_time"])
    end = min(a["end_time"], b["end_time"])
    overlap = max(0, end - start)
    min_duration = min(
        a["end_time"] - a["start_time"],
        b["end_time"] - b["start_time"],
    )
    if min_duration <= 0:
        return 0
    return overlap / min_duration
