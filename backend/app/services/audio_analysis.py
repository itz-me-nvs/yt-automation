"""
Audio energy and feature analysis service.

Uses librosa for audio feature extraction to detect:
- Energy peaks (exciting/loud moments - goals, reactions, drops)
- Tempo changes (music sections, action sequences)
- Spectral features (speech vs music vs effects)
- Onset detection (sudden sound events)

All processing is done locally using librosa (free, no API needed).
"""
import os
import logging
import subprocess
import tempfile
import numpy as np

logger = logging.getLogger(__name__)


def analyze_audio_energy(video_path: str, hop_length: int = 512, sr: int = 22050) -> dict:
    """
    Analyze audio energy levels throughout the video.

    Returns:
        dict with:
        - energy_timeline: list of {time, energy, is_peak} points
        - peaks: list of peak timestamps
        - avg_energy: average energy level
        - music_segments: detected music-heavy segments
    """
    try:
        import librosa

        # Extract audio to temp file
        audio_path = _extract_audio_to_temp(video_path)
        if not audio_path:
            return _empty_result()

        # Load audio with librosa
        y, sr_actual = librosa.load(audio_path, sr=sr, mono=True)

        # Compute RMS energy
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        times = librosa.times_like(rms, sr=sr_actual, hop_length=hop_length)

        # Normalize energy to 0-1 range
        if rms.max() > 0:
            rms_normalized = rms / rms.max()
        else:
            rms_normalized = rms

        # Detect energy peaks (moments significantly above average)
        avg_energy = float(np.mean(rms_normalized))
        std_energy = float(np.std(rms_normalized))
        peak_threshold = avg_energy + 1.5 * std_energy

        # Build timeline (sample every ~0.5 seconds for reasonable data size)
        sample_interval = max(1, int(0.5 * sr_actual / hop_length))
        energy_timeline = []
        for i in range(0, len(times), sample_interval):
            energy_val = float(rms_normalized[i])
            energy_timeline.append({
                "time": round(float(times[i]), 2),
                "energy": round(energy_val, 4),
                "is_peak": energy_val > peak_threshold,
            })

        # Find peak regions (contiguous high-energy areas)
        peaks = _find_peak_regions(times, rms_normalized, peak_threshold, min_duration=2.0)

        # Detect onset strength (sudden sound events)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr_actual)
        onset_times = librosa.times_like(onset_env, sr=sr_actual)

        # Spectral centroid to distinguish speech/music
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr_actual)[0]
        music_segments = _detect_music_segments(
            times, spectral_centroid[:len(times)], rms_normalized, sr_actual, hop_length
        )

        # Cleanup temp file
        try:
            os.unlink(audio_path)
        except OSError:
            pass

        return {
            "energy_timeline": energy_timeline,
            "peaks": peaks,
            "avg_energy": round(avg_energy, 4),
            "music_segments": music_segments,
            "duration": round(float(times[-1]) if len(times) > 0 else 0, 2),
        }

    except ImportError:
        logger.warning("librosa not available, using basic FFmpeg audio analysis")
        return _ffmpeg_audio_analysis(video_path)


def _extract_audio_to_temp(video_path: str) -> str | None:
    """Extract audio from video to a temporary WAV file."""
    try:
        temp_path = tempfile.mktemp(suffix=".wav")
        subprocess.run(
            [
                "ffmpeg", "-i", video_path,
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "22050", "-ac", "1",
                "-y", temp_path,
            ],
            capture_output=True, text=True, timeout=120
        )
        if os.path.exists(temp_path):
            return temp_path
    except Exception as e:
        logger.error(f"Audio extraction failed: {e}")
    return None


def _find_peak_regions(
    times: np.ndarray,
    energy: np.ndarray,
    threshold: float,
    min_duration: float = 2.0,
) -> list[dict]:
    """Find contiguous regions where energy exceeds the threshold."""
    peaks = []
    in_peak = False
    peak_start = 0.0

    for i in range(len(times)):
        if energy[i] > threshold and not in_peak:
            in_peak = True
            peak_start = float(times[i])
        elif energy[i] <= threshold and in_peak:
            in_peak = False
            peak_end = float(times[i])
            if peak_end - peak_start >= min_duration:
                peaks.append({
                    "start_time": round(peak_start, 2),
                    "end_time": round(peak_end, 2),
                    "duration": round(peak_end - peak_start, 2),
                    "max_energy": round(float(energy[
                        max(0, int(peak_start * len(energy) / float(times[-1]))):
                        min(len(energy), int(peak_end * len(energy) / float(times[-1])))
                    ].max()) if len(times) > 0 else 0, 4),
                })

    # Handle case where peak extends to end
    if in_peak and float(times[-1]) - peak_start >= min_duration:
        peaks.append({
            "start_time": round(peak_start, 2),
            "end_time": round(float(times[-1]), 2),
            "duration": round(float(times[-1]) - peak_start, 2),
            "max_energy": 1.0,
        })

    return peaks


def _detect_music_segments(
    times: np.ndarray,
    spectral_centroid: np.ndarray,
    energy: np.ndarray,
    sr: int,
    hop_length: int,
) -> list[dict]:
    """
    Detect segments that are likely music (vs speech).
    Music tends to have higher and more consistent spectral centroid
    with sustained energy, while speech has more variation.
    """
    segments = []
    min_len = min(len(times), len(spectral_centroid), len(energy))
    if min_len == 0:
        return segments

    # Normalize spectral centroid
    sc = spectral_centroid[:min_len]
    if sc.max() > 0:
        sc_norm = sc / sc.max()
    else:
        return segments

    # Music heuristic: high spectral centroid + sustained energy
    window_size = int(5.0 * sr / hop_length)  # 5 second window
    in_music = False
    music_start = 0.0

    for i in range(0, min_len - window_size, window_size // 2):
        window_sc = sc_norm[i:i + window_size]
        window_energy = energy[i:i + window_size]

        # Music: consistent high centroid and energy
        sc_std = float(np.std(window_sc))
        avg_energy = float(np.mean(window_energy))

        is_music = sc_std < 0.3 and avg_energy > 0.2

        if is_music and not in_music:
            in_music = True
            music_start = float(times[i])
        elif not is_music and in_music:
            in_music = False
            music_end = float(times[min(i + window_size, min_len - 1)])
            if music_end - music_start >= 5.0:
                segments.append({
                    "start_time": round(music_start, 2),
                    "end_time": round(music_end, 2),
                    "duration": round(music_end - music_start, 2),
                    "type": "music",
                })

    return segments


def _ffmpeg_audio_analysis(video_path: str) -> dict:
    """Basic audio analysis fallback using FFmpeg volumedetect."""
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-i", video_path,
                "-af", "volumedetect",
                "-f", "null", "-",
            ],
            capture_output=True, text=True, timeout=120
        )

        # Parse volume stats from FFmpeg output
        mean_volume = -30.0
        max_volume = -10.0
        for line in result.stderr.split("\n"):
            if "mean_volume:" in line:
                try:
                    mean_volume = float(line.split("mean_volume:")[1].split("dB")[0].strip())
                except ValueError:
                    pass
            elif "max_volume:" in line:
                try:
                    max_volume = float(line.split("max_volume:")[1].split("dB")[0].strip())
                except ValueError:
                    pass

        return {
            "energy_timeline": [],
            "peaks": [],
            "avg_energy": round((mean_volume + 90) / 90, 4),  # Normalize to 0-1
            "music_segments": [],
            "duration": 0,
        }
    except Exception:
        return _empty_result()


def _empty_result() -> dict:
    return {
        "energy_timeline": [],
        "peaks": [],
        "avg_energy": 0,
        "music_segments": [],
        "duration": 0,
    }
