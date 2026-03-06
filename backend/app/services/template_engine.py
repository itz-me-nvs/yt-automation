"""
Video overlay template engine.

Provides pre-built visual editing templates that can be applied to generated
YouTube Shorts using FFmpeg's drawtext, drawbox, and overlay filters.

Each template defines:
- Text overlays (position, style, animation, font)
- Background elements (gradient bars, blurred backgrounds)
- Timing (when text appears/disappears, animations)

Templates are designed for the football/sports niche but work with any content.
All rendering is done via FFmpeg filters - no external dependencies needed.

Template Categories:
- aura: "Ronaldo Aura", "Messi Magic" - dramatic centered text with glow
- hype: Bold impact text, high energy, big fonts
- commentary: Bottom-bar commentary style overlay
- stats: Player/match stats overlay card
- cinematic: Letterbox bars with elegant text
- minimal: Clean, small lower-third text
- versus: "Player A vs Player B" split design
- countdown: "Top 5 Goals" numbered overlay
"""
import os
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger(__name__)

# Path to bundled font (fallback to system fonts if not found)
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "fonts")

# FFmpeg drawtext escaping
def _escape_text(text: str) -> str:
    """Escape special characters for FFmpeg drawtext filter."""
    return text.replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:").replace("%", "%%")


@dataclass
class TextOverlay:
    """A single text element in a template."""
    text: str
    x: str = "(w-text_w)/2"   # Center horizontally by default
    y: str = "(h-text_h)/2"   # Center vertically by default
    fontsize: int = 72
    fontcolor: str = "white"
    font: str = "sans-serif"
    borderw: int = 3           # Text border/outline width
    bordercolor: str = "black"
    shadowx: int = 0
    shadowy: int = 0
    shadowcolor: str = "black@0.5"
    box: bool = False          # Draw background box
    boxcolor: str = "black@0.6"
    boxborderw: int = 20       # Padding inside box
    enable_expr: str = ""      # FFmpeg enable expression for timing, e.g. "between(t,1,5)"
    fade_in: float = 0.0       # Seconds for fade in
    fade_out: float = 0.0      # Seconds for fade out


@dataclass
class TemplateDefinition:
    """Complete template with metadata and overlay layers."""
    id: str
    name: str
    description: str
    category: str              # aura, hype, commentary, stats, cinematic, minimal, versus, countdown
    preview_color: str         # Hex color for UI preview
    text_layers: list[TextOverlay] = field(default_factory=list)
    # Additional FFmpeg filter chain to prepend (e.g., color grading, vignette)
    pre_filters: list[str] = field(default_factory=list)
    # Additional FFmpeg filter chain to append
    post_filters: list[str] = field(default_factory=list)
    # Whether this template needs the main_text and sub_text variables
    variables: list[str] = field(default_factory=lambda: ["main_text", "sub_text"])
    # Niche tags for filtering
    tags: list[str] = field(default_factory=lambda: ["football", "sports"])

    def to_dict(self) -> dict:
        d = asdict(self)
        d["text_layers"] = [asdict(layer) for layer in self.text_layers]
        return d


# ─────────────────────────────────────────────────────────────────────
# Built-in Template Definitions
# ─────────────────────────────────────────────────────────────────────

BUILTIN_TEMPLATES: dict[str, TemplateDefinition] = {}


def _register(template: TemplateDefinition):
    BUILTIN_TEMPLATES[template.id] = template


# ── 1. AURA TEMPLATE ────────────────────────────────────────────────
# Big centered text with glow/shadow effect. "Ronaldo Aura", "Prime Messi"
_register(TemplateDefinition(
    id="aura",
    name="Player Aura",
    description='Dramatic centered text with glow effect. Perfect for "Ronaldo Aura", "Prime Messi" style shorts.',
    category="aura",
    preview_color="#8B5CF6",
    variables=["main_text", "sub_text"],
    tags=["football", "sports", "player", "aura", "trending"],
    text_layers=[
        # Glow layer (large blurred shadow behind text)
        TextOverlay(
            text="{main_text}",
            x="(w-text_w)/2",
            y="(h-text_h)/2 - 40",
            fontsize=80,
            fontcolor="white@0.3",
            borderw=8,
            bordercolor="white@0.2",
            shadowx=0,
            shadowy=0,
            font="sans-serif",
        ),
        # Main text
        TextOverlay(
            text="{main_text}",
            x="(w-text_w)/2",
            y="(h-text_h)/2 - 40",
            fontsize=80,
            fontcolor="white",
            borderw=4,
            bordercolor="black@0.8",
            shadowx=3,
            shadowy=3,
            shadowcolor="black@0.7",
            font="sans-serif",
        ),
        # Sub text below
        TextOverlay(
            text="{sub_text}",
            x="(w-text_w)/2",
            y="(h-text_h)/2 + 60",
            fontsize=36,
            fontcolor="white@0.9",
            borderw=2,
            bordercolor="black@0.6",
            font="sans-serif",
        ),
    ],
    post_filters=[
        # Slight vignette for dramatic effect
        "vignette=PI/4",
    ],
))


# ── 2. HYPE TEMPLATE ────────────────────────────────────────────────
# Bold impact text, tilted feeling, high energy. For goal celebrations.
_register(TemplateDefinition(
    id="hype",
    name="Hype Moment",
    description="Bold impact text for high-energy moments. Goal celebrations, amazing skills.",
    category="hype",
    preview_color="#EF4444",
    variables=["main_text", "sub_text"],
    tags=["football", "sports", "goal", "celebration", "energy"],
    text_layers=[
        # Top accent bar
        TextOverlay(
            text="{sub_text}",
            x="(w-text_w)/2",
            y="120",
            fontsize=28,
            fontcolor="white",
            borderw=0,
            box=True,
            boxcolor="red@0.85",
            boxborderw=15,
            font="sans-serif",
        ),
        # Main LARGE text center
        TextOverlay(
            text="{main_text}",
            x="(w-text_w)/2",
            y="(h-text_h)/2",
            fontsize=96,
            fontcolor="white",
            borderw=5,
            bordercolor="red@0.9",
            shadowx=4,
            shadowy=4,
            shadowcolor="black@0.8",
            font="sans-serif",
        ),
    ],
))


# ── 3. COMMENTARY TEMPLATE ──────────────────────────────────────────
# Bottom bar with gradient, like a sports broadcast lower third.
_register(TemplateDefinition(
    id="commentary",
    name="Sports Commentary",
    description="Broadcast-style bottom bar. Clean lower-third like live TV commentary.",
    category="commentary",
    preview_color="#3B82F6",
    variables=["main_text", "sub_text"],
    tags=["football", "sports", "commentary", "broadcast", "professional"],
    pre_filters=[
        # Semi-transparent gradient bar at the bottom
        "drawbox=x=0:y=ih-220:w=iw:h=220:color=black@0.7:t=fill",
        # Accent line
        "drawbox=x=0:y=ih-220:w=iw:h=4:color=0x3B82F6@0.9:t=fill",
    ],
    text_layers=[
        # Main text on the bar
        TextOverlay(
            text="{main_text}",
            x="60",
            y="h - 180",
            fontsize=48,
            fontcolor="white",
            borderw=0,
            font="sans-serif",
        ),
        # Sub text smaller
        TextOverlay(
            text="{sub_text}",
            x="60",
            y="h - 110",
            fontsize=28,
            fontcolor="white@0.7",
            borderw=0,
            font="sans-serif",
        ),
    ],
))


# ── 4. CINEMATIC TEMPLATE ───────────────────────────────────────────
# Letterbox bars (top and bottom black bars) with centered elegant text.
_register(TemplateDefinition(
    id="cinematic",
    name="Cinematic",
    description="Widescreen letterbox bars with elegant centered text. Dramatic slow-mo moments.",
    category="cinematic",
    preview_color="#1F2937",
    variables=["main_text", "sub_text"],
    tags=["football", "sports", "cinematic", "dramatic", "slow-mo"],
    pre_filters=[
        # Top letterbox bar
        "drawbox=x=0:y=0:w=iw:h=180:color=black@0.95:t=fill",
        # Bottom letterbox bar
        "drawbox=x=0:y=ih-180:w=iw:h=180:color=black@0.95:t=fill",
    ],
    text_layers=[
        # Main text on bottom bar
        TextOverlay(
            text="{main_text}",
            x="(w-text_w)/2",
            y="h - 130",
            fontsize=44,
            fontcolor="white",
            borderw=0,
            font="sans-serif",
        ),
        # Sub text on top bar
        TextOverlay(
            text="{sub_text}",
            x="(w-text_w)/2",
            y="60",
            fontsize=24,
            fontcolor="white@0.6",
            borderw=0,
            font="sans-serif",
        ),
    ],
))


# ── 5. MINIMAL TEMPLATE ─────────────────────────────────────────────
# Clean, small text at the bottom. Non-intrusive.
_register(TemplateDefinition(
    id="minimal",
    name="Minimal Clean",
    description="Clean, minimal text at the bottom. Non-intrusive, lets the video speak.",
    category="minimal",
    preview_color="#6B7280",
    variables=["main_text"],
    tags=["football", "sports", "clean", "minimal", "simple"],
    text_layers=[
        TextOverlay(
            text="{main_text}",
            x="(w-text_w)/2",
            y="h - 200",
            fontsize=36,
            fontcolor="white",
            borderw=2,
            bordercolor="black@0.5",
            box=True,
            boxcolor="black@0.4",
            boxborderw=12,
            font="sans-serif",
        ),
    ],
))


# ── 6. VERSUS TEMPLATE ──────────────────────────────────────────────
# "Player A vs Player B" - split text design with VS in the middle.
_register(TemplateDefinition(
    id="versus",
    name="Versus Battle",
    description="Player vs Player comparison. Split design with VS in the middle.",
    category="versus",
    preview_color="#F59E0B",
    variables=["main_text", "sub_text"],
    tags=["football", "sports", "comparison", "versus", "battle"],
    pre_filters=[
        # Dark overlay at the center band
        "drawbox=x=0:y=ih/2-120:w=iw:h=240:color=black@0.75:t=fill",
    ],
    text_layers=[
        # Left/top name
        TextOverlay(
            text="{main_text}",
            x="(w-text_w)/2",
            y="h/2 - 90",
            fontsize=52,
            fontcolor="white",
            borderw=3,
            bordercolor="black",
            font="sans-serif",
        ),
        # VS text
        TextOverlay(
            text="VS",
            x="(w-text_w)/2",
            y="(h-text_h)/2",
            fontsize=40,
            fontcolor="#F59E0B",
            borderw=3,
            bordercolor="black",
            font="sans-serif",
        ),
        # Right/bottom name
        TextOverlay(
            text="{sub_text}",
            x="(w-text_w)/2",
            y="h/2 + 50",
            fontsize=52,
            fontcolor="white",
            borderw=3,
            bordercolor="black",
            font="sans-serif",
        ),
    ],
))


# ── 7. COUNTDOWN TEMPLATE ───────────────────────────────────────────
# "Top 5 Goals" numbered overlay.
_register(TemplateDefinition(
    id="countdown",
    name="Countdown / Top N",
    description='Numbered ranking overlay. Perfect for "Top 5 Goals", "Best Saves" compilations.',
    category="countdown",
    preview_color="#10B981",
    variables=["main_text", "sub_text"],
    tags=["football", "sports", "top", "ranking", "compilation"],
    pre_filters=[
        # Number circle background area
        "drawbox=x=30:y=30:w=120:h=120:color=red@0.9:t=fill",
    ],
    text_layers=[
        # Big number in the top-left circle
        TextOverlay(
            text="{main_text}",
            x="50",
            y="40",
            fontsize=80,
            fontcolor="white",
            borderw=0,
            font="sans-serif",
        ),
        # Description text at bottom
        TextOverlay(
            text="{sub_text}",
            x="(w-text_w)/2",
            y="h - 160",
            fontsize=38,
            fontcolor="white",
            borderw=2,
            bordercolor="black@0.7",
            box=True,
            boxcolor="black@0.5",
            boxborderw=15,
            font="sans-serif",
        ),
    ],
))


# ── 8. GOAL FLASH TEMPLATE ──────────────────────────────────────────
# Red flash overlay with "GOAAAL!" style text.
_register(TemplateDefinition(
    id="goal_flash",
    name="Goal Flash",
    description='Intense flash overlay with bold "GOAAAL!" style. For goal moments.',
    category="hype",
    preview_color="#DC2626",
    variables=["main_text", "sub_text"],
    tags=["football", "goal", "celebration", "flash", "intense"],
    pre_filters=[
        # Red tint border frame
        "drawbox=x=0:y=0:w=iw:h=8:color=red@0.9:t=fill",
        "drawbox=x=0:y=ih-8:w=iw:h=8:color=red@0.9:t=fill",
        "drawbox=x=0:y=0:w=8:h=ih:color=red@0.9:t=fill",
        "drawbox=x=iw-8:y=0:w=8:h=ih:color=red@0.9:t=fill",
    ],
    text_layers=[
        # Shadow layer
        TextOverlay(
            text="{main_text}",
            x="(w-text_w)/2 + 4",
            y="(h-text_h)/2 + 4",
            fontsize=100,
            fontcolor="red@0.5",
            borderw=0,
            font="sans-serif",
        ),
        # Main GOAAAL text
        TextOverlay(
            text="{main_text}",
            x="(w-text_w)/2",
            y="(h-text_h)/2",
            fontsize=100,
            fontcolor="white",
            borderw=5,
            bordercolor="red",
            font="sans-serif",
        ),
        # Scorer name
        TextOverlay(
            text="{sub_text}",
            x="(w-text_w)/2",
            y="(h-text_h)/2 + 100",
            fontsize=36,
            fontcolor="white@0.9",
            borderw=2,
            bordercolor="black@0.6",
            font="sans-serif",
        ),
    ],
))


# ─────────────────────────────────────────────────────────────────────
# Template Rendering (FFmpeg filter chain builder)
# ─────────────────────────────────────────────────────────────────────

def get_all_templates() -> list[dict]:
    """Return all templates as dicts (for API response)."""
    return [t.to_dict() for t in BUILTIN_TEMPLATES.values()]


def get_template(template_id: str) -> Optional[TemplateDefinition]:
    """Get a template by ID."""
    return BUILTIN_TEMPLATES.get(template_id)


def build_template_filters(
    template_id: str,
    variables: dict[str, str],
) -> list[str]:
    """
    Build FFmpeg filter chain strings for a template with variable substitution.

    Args:
        template_id: Template ID
        variables: Dict of variable values, e.g. {"main_text": "GOAAAL!", "sub_text": "Ronaldo 90'"}

    Returns:
        List of FFmpeg filter strings to be joined with ","
    """
    template = get_template(template_id)
    if not template:
        logger.warning(f"Template '{template_id}' not found")
        return []

    filters = []

    # Pre-filters (boxes, overlays, color grading)
    filters.extend(template.pre_filters)

    # Text layers
    for layer in template.text_layers:
        # Substitute variables in text
        text = layer.text
        for var_name, var_value in variables.items():
            text = text.replace(f"{{{var_name}}}", var_value)

        escaped_text = _escape_text(text)

        # Build drawtext filter
        parts = [
            f"text='{escaped_text}'",
            f"x={layer.x}",
            f"y={layer.y}",
            f"fontsize={layer.fontsize}",
            f"fontcolor={layer.fontcolor}",
            f"borderw={layer.borderw}",
            f"bordercolor={layer.bordercolor}",
            f"shadowx={layer.shadowx}",
            f"shadowy={layer.shadowy}",
            f"shadowcolor={layer.shadowcolor}",
        ]

        # Add font if not default
        if layer.font and layer.font != "sans-serif":
            parts.append(f"fontfile={layer.font}")

        # Box background
        if layer.box:
            parts.append(f"box=1")
            parts.append(f"boxcolor={layer.boxcolor}")
            parts.append(f"boxborderw={layer.boxborderw}")

        # Timing
        if layer.enable_expr:
            parts.append(f"enable='{layer.enable_expr}'")

        filters.append("drawtext=" + ":".join(parts))

    # Post-filters (vignette, color grading)
    filters.extend(template.post_filters)

    return filters


def generate_template_suggestions(
    highlight: dict,
    categories: dict,
) -> list[dict]:
    """
    Suggest appropriate templates for a highlight based on its content.

    Uses the highlight category, keywords, and content analysis to pick
    the best matching templates.

    Returns:
        List of {"template_id", "main_text", "sub_text", "confidence"} suggestions
    """
    category = highlight.get("category", "").lower()
    title = highlight.get("title", "")
    description = highlight.get("description", "")
    text = f"{title} {description}".lower()

    suggestions = []

    # Football-specific keyword detection
    goal_words = {"goal", "score", "scored", "goaaal", "finish", "strike", "volley", "header"}
    skill_words = {"skill", "dribble", "trick", "nutmeg", "rainbow", "flick", "tekkers"}
    player_words = {"ronaldo", "messi", "neymar", "mbappe", "haaland", "salah", "vinicius",
                    "bellingham", "modric", "kroos", "benzema", "lewandowski", "de bruyne"}
    aura_words = {"aura", "prime", "goat", "legend", "beast", "king", "magic", "genius"}
    vs_words = {"vs", "versus", "against", "battle", "rivalry", "derby", "clash"}

    text_words = set(text.split())

    # Detect player names in the text
    detected_players = text_words & player_words
    detected_player = detected_players.pop().title() if detected_players else ""

    # Goal moment -> Goal Flash or Hype
    if text_words & goal_words:
        suggestions.append({
            "template_id": "goal_flash",
            "main_text": "GOAAAL!",
            "sub_text": detected_player or title[:40],
            "confidence": 0.95,
        })
        suggestions.append({
            "template_id": "hype",
            "main_text": title[:30] or "WHAT A GOAL!",
            "sub_text": detected_player or "Incredible finish",
            "confidence": 0.85,
        })

    # Player aura / skill
    if text_words & (aura_words | skill_words) or detected_player:
        player_name = detected_player or "THE GOAT"
        suggestions.append({
            "template_id": "aura",
            "main_text": f"{player_name} Aura",
            "sub_text": "Different breed entirely",
            "confidence": 0.9,
        })

    # Versus / comparison
    if text_words & vs_words:
        suggestions.append({
            "template_id": "versus",
            "main_text": title.split(" vs ")[0][:25] if " vs " in title.lower() else title[:25],
            "sub_text": title.split(" vs ")[-1][:25] if " vs " in title.lower() else "The Rival",
            "confidence": 0.9,
        })

    # Exciting / dramatic -> Hype
    if category in ("exciting", "dramatic"):
        suggestions.append({
            "template_id": "hype",
            "main_text": title[:30] or "INCREDIBLE!",
            "sub_text": description[:40] or "You won't believe this",
            "confidence": 0.8,
        })

    # Emotional -> Cinematic
    if category == "emotional":
        suggestions.append({
            "template_id": "cinematic",
            "main_text": title[:40] or "Emotional Moment",
            "sub_text": detected_player or "Football is beautiful",
            "confidence": 0.85,
        })

    # Commentary style for informative content
    if category == "informative":
        suggestions.append({
            "template_id": "commentary",
            "main_text": title[:40] or "Breaking Down the Play",
            "sub_text": description[:50] or "Tactical analysis",
            "confidence": 0.8,
        })

    # Always include minimal as a safe fallback
    suggestions.append({
        "template_id": "minimal",
        "main_text": title[:40] or "Watch This",
        "sub_text": "",
        "confidence": 0.5,
    })

    # Always include aura if we found a player and haven't already
    if detected_player and not any(s["template_id"] == "aura" for s in suggestions):
        suggestions.append({
            "template_id": "aura",
            "main_text": f"Prime {detected_player}",
            "sub_text": "This is why he's the GOAT",
            "confidence": 0.75,
        })

    # Sort by confidence and deduplicate by template_id
    seen = set()
    unique = []
    for s in sorted(suggestions, key=lambda x: x["confidence"], reverse=True):
        if s["template_id"] not in seen:
            seen.add(s["template_id"])
            unique.append(s)

    return unique[:5]


def generate_llm_template_prompt(highlight: dict) -> str:
    """
    Build a prompt for the local LLM to generate creative overlay text
    for a specific highlight.
    """
    return f"""You are a viral YouTube Shorts editor specializing in football content.

Given this video highlight, suggest the best overlay text for a YouTube Short.

Highlight:
- Title: {highlight.get('title', 'Unknown')}
- Category: {highlight.get('category', 'general')}
- Description: {highlight.get('description', '')}
- Duration: {highlight.get('duration', 0):.0f} seconds

Generate overlay text in this JSON format:
{{
  "main_text": "<big bold text, max 20 chars, catchy, e.g. 'Ronaldo Aura', 'GOAAAL!', 'Prime Messi'>",
  "sub_text": "<smaller supporting text, max 40 chars, e.g. 'Different breed entirely', 'What a strike!'>",
  "style": "<one of: aura, hype, goal_flash, cinematic, commentary, minimal, versus, countdown>"
}}

Rules:
- main_text must be SHORT and PUNCHY (2-4 words max)
- Use football slang: aura, prime, goat, beast, tekkers, worldie
- Make it trendy and viral-worthy
- Match the energy of the moment
- Respond ONLY with JSON"""
