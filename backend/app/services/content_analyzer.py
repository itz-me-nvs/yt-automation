"""
Content analysis service using local LLMs via Ollama.

Uses Ollama to run local language models for:
- Analyzing transcript to identify highlights, emotions, and categories
- Generating titles and descriptions for short clips
- Summarizing video content

Supported Ollama models (all free, run locally):
- llama3.2: General purpose, good for text analysis
- mistral: Fast, good for classification tasks
- gemma2: Google's model, strong at understanding

Also uses CLIP (Contrastive Language-Image Pre-training) for visual analysis:
- Classifies scene frames into categories
- Detects visual content type (sports, music, comedy, etc.)
- Runs locally via transformers library
"""
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


async def analyze_transcript_with_llm(
    transcript: str,
    segments: list[dict],
    video_duration: float,
) -> dict:
    """
    Use a local LLM (via Ollama) to analyze the transcript and identify
    highlight-worthy moments.

    Returns:
        dict with highlights, emotions, categories, and summary
    """
    if not transcript or not transcript.strip():
        return {
            "highlights": [],
            "emotions": [],
            "categories": {},
            "summary": "No transcript available for analysis.",
        }

    try:
        import ollama

        # Build analysis prompt with the transcript
        prompt = _build_analysis_prompt(transcript, segments, video_duration)

        # Call Ollama local LLM
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert video content analyst. Analyze the transcript "
                        "and identify the best moments for YouTube Shorts. "
                        "Respond ONLY with valid JSON, no other text."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            options={"temperature": 0.3, "num_predict": 4096},
        )

        response_text = response["message"]["content"]
        return _parse_llm_response(response_text, segments)

    except ImportError:
        logger.warning("Ollama Python client not available")
        return _rule_based_analysis(transcript, segments, video_duration)
    except Exception as e:
        logger.warning(f"Ollama analysis failed (is Ollama running?): {e}")
        logger.info("Falling back to rule-based analysis")
        return _rule_based_analysis(transcript, segments, video_duration)


def _build_analysis_prompt(
    transcript: str, segments: list[dict], duration: float,
) -> str:
    """Build the prompt for LLM analysis."""
    # Format segments with timestamps
    timestamped_text = ""
    for seg in segments[:200]:  # Limit to avoid token overflow
        start = seg["start"]
        end = seg["end"]
        text = seg["text"]
        timestamped_text += f"[{_format_time(start)} - {_format_time(end)}] {text}\n"

    return f"""Analyze this video transcript (duration: {_format_time(duration)}) and identify the best moments for YouTube Shorts (15-60 seconds each).

This is likely a FOOTBALL/SOCCER video. Pay special attention to:
- Goal moments (celebrations, commentary excitement)
- Skill moves, dribbles, tricks, nutmegs
- Player highlights (Ronaldo, Messi, Neymar, etc.)
- Emotional reactions (crowd, players, managers)
- Dramatic moments (last-minute goals, red cards, penalties)
- Funny/entertaining moments
- Match turning points

TRANSCRIPT WITH TIMESTAMPS:
{timestamped_text}

Return a JSON object with this exact structure:
{{
  "highlights": [
    {{
      "start_time": <seconds>,
      "end_time": <seconds>,
      "category": "<goal|skill|funny|emotional|exciting|informative|music|dramatic>",
      "title": "<short catchy title>",
      "description": "<why this is a good short>",
      "score": <0.0-1.0 indicating how good this highlight is>,
      "reasons": ["<reason1>", "<reason2>"],
      "overlay_text": "<2-4 word punchy text for video overlay, e.g. 'Ronaldo Aura', 'GOAAAL!', 'Prime Messi'>",
      "overlay_subtext": "<short supporting text, e.g. 'Different breed', 'What a strike!'>"
    }}
  ],
  "emotions": [
    {{
      "start_time": <seconds>,
      "end_time": <seconds>,
      "emotion": "<happy|sad|excited|angry|surprised|neutral>",
      "intensity": <0.0-1.0>,
      "text": "<the text in this segment>"
    }}
  ],
  "categories": {{
    "primary": "<main category of the video>",
    "tags": ["<tag1>", "<tag2>", ...],
    "content_type": "<entertainment|education|sports|music|gaming|vlog|news>",
    "players_mentioned": ["<player names found in transcript>"],
    "teams_mentioned": ["<team names found in transcript>"]
  }},
  "summary": "<2-3 sentence summary of the video>"
}}

Find at least 3-5 highlights. Prioritize:
1. Goal moments and celebrations
2. Amazing skills, dribbles, and tricks
3. Emotional peaks (dramatic reactions, crowd moments)
4. Funny/entertaining moments
5. Player "aura" moments (dominance, confidence, flair)
6. Action/exciting moments (saves, tackles, counter-attacks)"""


def _parse_llm_response(response_text: str, segments: list[dict]) -> dict:
    """Parse the LLM's JSON response, handling potential formatting issues."""
    # Try to extract JSON from the response
    try:
        # Try direct parse first
        data = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        try:
            start = response_text.index("{")
            end = response_text.rindex("}") + 1
            data = json.loads(response_text[start:end])
        except (ValueError, json.JSONDecodeError):
            logger.warning("Could not parse LLM response as JSON")
            return _rule_based_analysis("", segments, 0)

    # Validate and normalize the response
    highlights = []
    for h in data.get("highlights", []):
        highlights.append({
            "start_time": float(h.get("start_time", 0)),
            "end_time": float(h.get("end_time", 0)),
            "duration": float(h.get("end_time", 0)) - float(h.get("start_time", 0)),
            "category": h.get("category", "general"),
            "title": h.get("title", "Highlight"),
            "description": h.get("description", ""),
            "score": min(1.0, max(0.0, float(h.get("score", 0.5)))),
            "reasons": h.get("reasons", []),
            "overlay_text": h.get("overlay_text", ""),
            "overlay_subtext": h.get("overlay_subtext", ""),
        })

    emotions = []
    for e in data.get("emotions", []):
        emotions.append({
            "start_time": float(e.get("start_time", 0)),
            "end_time": float(e.get("end_time", 0)),
            "emotion": e.get("emotion", "neutral"),
            "intensity": min(1.0, max(0.0, float(e.get("intensity", 0.5)))),
            "text": e.get("text", ""),
        })

    return {
        "highlights": highlights,
        "emotions": emotions,
        "categories": data.get("categories", {}),
        "summary": data.get("summary", ""),
    }


def _rule_based_analysis(
    transcript: str, segments: list[dict], duration: float,
) -> dict:
    """
    Rule-based fallback analysis when LLM is not available.
    Uses keyword matching and heuristics to find highlights.
    """
    logger.info("Running rule-based content analysis")

    # Football/sports-focused keyword sets
    goal_words = {
        "goal", "score", "scored", "finish", "strike", "volley", "header",
        "penalty", "free kick", "freekick", "net", "keeper", "saved",
    }
    excitement_words = {
        "goal", "score", "win", "amazing", "incredible", "wow", "unbelievable",
        "fantastic", "brilliant", "perfect", "yes", "champion", "victory",
        "worldie", "banger", "screamer", "rocket", "thunderbolt",
    }
    skill_words = {
        "skill", "dribble", "trick", "nutmeg", "rainbow", "flick", "tekkers",
        "touch", "control", "pass", "assist", "through", "chip", "lob",
    }
    funny_words = {
        "haha", "lol", "funny", "laugh", "hilarious", "joke", "comedy",
        "ridiculous", "silly", "crazy", "lmao", "rofl", "dive", "flop",
    }
    emotional_words = {
        "love", "cry", "tears", "beautiful", "heart", "miss", "remember",
        "goodbye", "sorry", "hope", "dream", "believe", "forever",
        "legend", "retire", "farewell", "tribute", "respect",
    }
    dramatic_words = {
        "no", "stop", "wait", "what", "oh", "omg", "shocked", "breaking",
        "urgent", "just", "finally", "never", "always", "red card",
        "offside", "var", "injury", "foul", "last minute",
    }
    player_names = {
        "ronaldo", "messi", "neymar", "mbappe", "haaland", "salah",
        "vinicius", "bellingham", "modric", "kroos", "benzema",
        "lewandowski", "de bruyne", "palmer", "saka", "foden",
    }

    highlights = []
    emotions = []

    for seg in segments:
        text_lower = seg["text"].lower()
        words = set(text_lower.split())

        # Check each category
        goal_score = len(words & goal_words) / max(len(words), 1)
        excitement_score = len(words & excitement_words) / max(len(words), 1)
        skill_score = len(words & skill_words) / max(len(words), 1)
        funny_score = len(words & funny_words) / max(len(words), 1)
        emotional_score = len(words & emotional_words) / max(len(words), 1)
        dramatic_score = len(words & dramatic_words) / max(len(words), 1)

        # Detect player names for overlay text
        detected_players = words & player_names
        player_name = detected_players.pop().title() if detected_players else ""

        all_scores = {
            "goal": goal_score,
            "exciting": excitement_score,
            "skill": skill_score,
            "funny": funny_score,
            "emotional": emotional_score,
            "dramatic": dramatic_score,
        }
        max_category = max(all_scores, key=all_scores.get)
        max_score = all_scores[max_category]

        if max_score > 0.05:
            category = max_category
            emotion_map = {
                "goal": "excited", "exciting": "excited", "skill": "excited",
                "funny": "happy", "emotional": "sad", "dramatic": "surprised",
            }
            emotion = emotion_map.get(category, "neutral")

            # Generate overlay text based on category
            overlay_map = {
                "goal": ("GOAAAL!", player_name or "What a finish!"),
                "exciting": ("INCREDIBLE!", player_name or "Unbelievable moment"),
                "skill": (f"{player_name} Aura" if player_name else "TEKKERS!", "Different breed"),
                "funny": ("NO WAY!", "You can't be serious"),
                "emotional": (f"Legend {player_name}" if player_name else "Beautiful Game", "Football is life"),
                "dramatic": ("DRAMA!", player_name or "What just happened?!"),
            }
            overlay_text, overlay_subtext = overlay_map.get(category, ("Watch This", ""))

            highlights.append({
                "start_time": seg["start"],
                "end_time": seg["end"],
                "duration": seg["end"] - seg["start"],
                "category": category,
                "title": f"{category.title()} Moment" + (f" - {player_name}" if player_name else ""),
                "description": seg["text"][:100],
                "score": min(1.0, max_score * 5),
                "reasons": [f"Contains {category} keywords"] + ([f"Player: {player_name}"] if player_name else []),
                "overlay_text": overlay_text,
                "overlay_subtext": overlay_subtext,
            })

            emotions.append({
                "start_time": seg["start"],
                "end_time": seg["end"],
                "emotion": emotion,
                "intensity": min(1.0, max_score * 5),
                "text": seg["text"],
            })

    # Sort by score and keep top highlights
    highlights.sort(key=lambda x: x["score"], reverse=True)
    highlights = highlights[:10]

    # Determine categories
    category_counts = {}
    for h in highlights:
        cat = h["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    primary_category = max(category_counts, key=category_counts.get) if category_counts else "general"

    return {
        "highlights": highlights,
        "emotions": emotions,
        "categories": {
            "primary": primary_category,
            "tags": list(category_counts.keys()),
            "content_type": "entertainment",
        },
        "summary": f"Video contains {len(highlights)} notable moments across {len(category_counts)} categories.",
    }


async def analyze_frames_with_clip(frame_paths: list[str]) -> list[dict]:
    """
    Analyze extracted video frames using CLIP model for visual content classification.

    CLIP (Contrastive Language-Image Pre-training) by OpenAI:
    - Understands images in terms of natural language descriptions
    - Can classify images into arbitrary categories without training
    - Runs locally via the transformers library

    Args:
        frame_paths: List of paths to extracted frame images

    Returns:
        List of dicts with frame classifications
    """
    categories = [
        "a football goal or celebration",
        "a football skill move or dribble",
        "a football tackle or defensive play",
        "a sports highlight or exciting moment",
        "a funny or comedic moment",
        "an emotional or dramatic scene",
        "a person talking to camera or interview",
        "a crowd or stadium reaction",
    ]

    try:
        from transformers import CLIPProcessor, CLIPModel
        from PIL import Image

        # Load CLIP model (cached after first load)
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        results = []
        for frame_path in frame_paths:
            if frame_path is None or not os.path.exists(frame_path):
                results.append({"categories": {}, "primary": "unknown"})
                continue

            image = Image.open(frame_path).convert("RGB")
            inputs = processor(text=categories, images=image, return_tensors="pt", padding=True)
            outputs = model(**inputs)

            # Get probability for each category
            logits = outputs.logits_per_image[0]
            probs = logits.softmax(dim=0).tolist()

            category_scores = {}
            for cat, prob in zip(categories, probs):
                short_cat = cat.split("a ")[-1].split(" or ")[0]
                category_scores[short_cat] = round(prob, 4)

            primary = max(category_scores, key=category_scores.get)
            results.append({
                "categories": category_scores,
                "primary": primary,
            })

        return results

    except ImportError:
        logger.warning("CLIP/transformers not available for visual analysis")
        return [{"categories": {}, "primary": "unknown"} for _ in frame_paths]
    except Exception as e:
        logger.error(f"CLIP analysis failed: {e}")
        return [{"categories": {}, "primary": "unknown"} for _ in frame_paths]


def _format_time(seconds: float) -> str:
    """Format seconds as MM:SS."""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes:02d}:{secs:02d}"
