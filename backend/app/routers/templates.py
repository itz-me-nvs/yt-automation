"""
Templates API routes.
Handles listing templates, getting suggestions, regenerating shorts with
different templates, and managing custom/saved templates.
"""
import uuid
import json
import asyncio
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..database import get_db
from ..models.schemas import (
    TemplateResponse,
    TemplateSuggestion,
    RegenerateShortRequest,
    ShortResponse,
    CustomTemplateCreate,
)
from ..services.template_engine import (
    get_all_templates,
    get_template,
    generate_template_suggestions,
    BUILTIN_TEMPLATES,
)
from ..services.shorts_generator import generate_short

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/", response_model=list[TemplateResponse])
async def list_templates():
    """List all available overlay templates."""
    templates = []
    for t in BUILTIN_TEMPLATES.values():
        templates.append(TemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            category=t.category,
            preview_color=t.preview_color,
            variables=t.variables,
            tags=t.tags,
        ))
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template_detail(template_id: str):
    """Get details of a specific template."""
    t = get_template(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse(
        id=t.id,
        name=t.name,
        description=t.description,
        category=t.category,
        preview_color=t.preview_color,
        variables=t.variables,
        tags=t.tags,
    )


@router.get("/suggest/{video_id}", response_model=list[TemplateSuggestion])
async def suggest_templates(video_id: str, highlight_index: int = 0):
    """
    Get AI-powered template suggestions for a specific highlight.
    Uses the highlight's content, category, and detected keywords to
    suggest the best matching templates with pre-filled text.
    """
    db = await get_db()

    # Get analysis results
    cursor = await db.execute(
        "SELECT highlights_json, categories_json FROM analysis_results WHERE video_id = ? ORDER BY created_at DESC LIMIT 1",
        (video_id,),
    )
    analysis = await cursor.fetchone()
    await db.close()

    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis results found")

    highlights = json.loads(analysis["highlights_json"] or "[]")
    categories = json.loads(analysis["categories_json"] or "{}")

    if highlight_index >= len(highlights):
        raise HTTPException(status_code=400, detail=f"Highlight index {highlight_index} out of range")

    highlight = highlights[highlight_index]
    suggestions = generate_template_suggestions(highlight, categories)

    return [
        TemplateSuggestion(**s) for s in suggestions
    ]


@router.post("/regenerate", response_model=ShortResponse)
async def regenerate_short_with_template(
    request: RegenerateShortRequest,
    background_tasks: BackgroundTasks,
):
    """
    Regenerate a short clip with a different template and custom text.
    This lets users pick a different template or customize the overlay text
    after the initial auto-generation.
    """
    db = await get_db()

    # Get video info
    cursor = await db.execute(
        "SELECT * FROM videos WHERE id = ?", (request.video_id,)
    )
    video = await cursor.fetchone()
    if not video:
        await db.close()
        raise HTTPException(status_code=404, detail="Video not found")

    # Get analysis to find the highlight
    cursor = await db.execute(
        "SELECT highlights_json FROM analysis_results WHERE video_id = ? ORDER BY created_at DESC LIMIT 1",
        (request.video_id,),
    )
    analysis = await cursor.fetchone()
    if not analysis:
        await db.close()
        raise HTTPException(status_code=404, detail="No analysis results found")

    highlights = json.loads(analysis["highlights_json"] or "[]")
    if request.highlight_index >= len(highlights):
        await db.close()
        raise HTTPException(status_code=400, detail="Invalid highlight index")

    highlight = highlights[request.highlight_index]

    # Validate template
    template = get_template(request.template_id)
    if not template:
        await db.close()
        raise HTTPException(status_code=404, detail=f"Template '{request.template_id}' not found")

    # Generate the short with the new template
    short_id = str(uuid.uuid4())
    template_vars = {
        "main_text": request.main_text,
        "sub_text": request.sub_text,
    }

    try:
        result = await asyncio.to_thread(
            generate_short,
            video_path=video["file_path"],
            start_time=highlight["start_time"],
            end_time=highlight["end_time"],
            short_id=short_id,
            title=highlight.get("title", "Short"),
            template_id=request.template_id,
            template_variables=template_vars,
        )

        # Save to database
        await db.execute(
            """INSERT INTO shorts
               (id, video_id, title, description,
                start_time, end_time, duration, category, score,
                file_path, thumbnail_path, template_id,
                template_variables_json, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed')""",
            (
                short_id,
                request.video_id,
                highlight.get("title", "Short"),
                highlight.get("description", ""),
                highlight.get("start_time", 0),
                highlight.get("end_time", 0),
                result.get("duration", 0),
                highlight.get("category", "general"),
                highlight.get("score", 0),
                result.get("file_path", ""),
                result.get("thumbnail_path"),
                request.template_id,
                json.dumps(template_vars),
            ),
        )
        await db.commit()
        await db.close()

        return ShortResponse(
            id=short_id,
            video_id=request.video_id,
            title=highlight.get("title", "Short"),
            description=highlight.get("description", ""),
            start_time=highlight.get("start_time", 0),
            end_time=highlight.get("end_time", 0),
            duration=result.get("duration", 0),
            category=highlight.get("category", "general"),
            score=highlight.get("score", 0),
            file_path=result.get("file_path"),
            thumbnail_path=result.get("thumbnail_path"),
            template_id=request.template_id,
            template_variables=template_vars,
            status="completed",
            created_at="",
        )

    except Exception as e:
        await db.close()
        logger.error(f"Regeneration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Custom / Saved Templates ────────────────────────────────────────

@router.get("/custom/list")
async def list_custom_templates():
    """List user's saved custom templates."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM custom_templates ORDER BY usage_count DESC, created_at DESC"
    )
    rows = await cursor.fetchall()
    await db.close()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "category": row["category"],
            "base_template_id": row["base_template_id"],
            "variables": json.loads(row["variables_json"] or "{}"),
            "is_favorite": bool(row["is_favorite"]),
            "usage_count": row["usage_count"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


@router.post("/custom")
async def save_custom_template(template: CustomTemplateCreate):
    """Save a custom template preset (base template + custom text variables)."""
    template_id = str(uuid.uuid4())

    # Validate base template exists
    if not get_template(template.base_template_id):
        raise HTTPException(status_code=404, detail=f"Base template '{template.base_template_id}' not found")

    db = await get_db()
    await db.execute(
        """INSERT INTO custom_templates
           (id, name, description, category, base_template_id, variables_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            template_id,
            template.name,
            template.description,
            template.category,
            template.base_template_id,
            json.dumps(template.variables),
        ),
    )
    await db.commit()
    await db.close()

    return {"id": template_id, "message": "Custom template saved"}


@router.delete("/custom/{template_id}")
async def delete_custom_template(template_id: str):
    """Delete a custom template."""
    db = await get_db()
    await db.execute("DELETE FROM custom_templates WHERE id = ?", (template_id,))
    await db.commit()
    await db.close()
    return {"message": "Custom template deleted"}
