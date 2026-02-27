"""
Audio transcription service using OpenAI Whisper (local, free model).

Whisper is a general-purpose speech recognition model trained on 680,000 hours
of multilingual data. It runs entirely locally - no API keys needed.

Models available (smallest to largest):
- tiny: ~39M params, fastest, least accurate
- base: ~74M params, good balance for quick processing
- small: ~244M params, better accuracy
- medium: ~769M params, high accuracy
- large: ~1.55B params, best accuracy (requires significant GPU memory)

We default to 'base' for speed, configurable via environment variable.
"""
import os
import subprocess
import json
import logging
import tempfile

logger = logging.getLogger(__name__)

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")


def extract_audio(video_path: str, output_path: str = None) -> str:
    """Extract audio from video file using FFmpeg."""
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".wav")

    subprocess.run(
        [
            "ffmpeg", "-i", video_path,
            "-vn",  # no video
            "-acodec", "pcm_s16le",  # WAV format
            "-ar", "16000",  # 16kHz sample rate (Whisper's native rate)
            "-ac", "1",  # mono
            "-y",  # overwrite
            output_path,
        ],
        capture_output=True, text=True, timeout=300
    )

    if not os.path.exists(output_path):
        raise RuntimeError("Audio extraction failed")

    return output_path


def transcribe_audio(video_path: str, model_size: str = None) -> dict:
    """
    Transcribe audio from a video file using Whisper.

    Returns:
        dict with keys:
        - text: full transcript text
        - segments: list of {start, end, text} dicts with timestamps
        - language: detected language
    """
    if model_size is None:
        model_size = WHISPER_MODEL

    logger.info(f"Transcribing with Whisper model: {model_size}")

    try:
        import whisper

        # Load model (cached after first load)
        model = whisper.load_model(model_size)

        # Transcribe with word-level timestamps
        result = model.transcribe(
            video_path,
            verbose=False,
            word_timestamps=True,
            task="transcribe",
        )

        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg["text"].strip(),
            })

        return {
            "text": result.get("text", "").strip(),
            "segments": segments,
            "language": result.get("language", "unknown"),
        }

    except ImportError:
        logger.warning("Whisper not available, falling back to ffmpeg-based extraction")
        return _fallback_transcribe(video_path)


def _fallback_transcribe(video_path: str) -> dict:
    """Fallback transcription when Whisper is not available."""
    logger.info("Using fallback transcription (no ML - returns empty)")
    return {
        "text": "",
        "segments": [],
        "language": "unknown",
    }


def get_word_timestamps(video_path: str) -> list[dict]:
    """Get word-level timestamps for precise highlight cutting."""
    try:
        import whisper

        model = whisper.load_model(WHISPER_MODEL)
        result = model.transcribe(video_path, word_timestamps=True)

        words = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                words.append({
                    "word": word_info["word"].strip(),
                    "start": round(word_info["start"], 3),
                    "end": round(word_info["end"], 3),
                })

        return words

    except ImportError:
        return []
