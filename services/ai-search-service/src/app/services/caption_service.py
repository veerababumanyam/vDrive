"""Caption generation service using Gemini for intelligent photo captions."""

from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.llm import generate_text
from ..models import Caption, CaptionStyle

logger = structlog.get_logger()

# Prompts for different caption styles
CAPTION_PROMPTS = {
    CaptionStyle.PROFESSIONAL: """Generate a professional, polished caption for this photograph.
The caption should be suitable for a professional portfolio or client delivery.
Focus on composition, lighting, and emotional impact.
Keep it concise but impactful (1-2 sentences).""",
    CaptionStyle.CASUAL: """Generate a casual, friendly caption for this photograph.
The caption should feel natural and personable.
Use conversational language without being too informal.
Keep it brief and relatable.""",
    CaptionStyle.SEO: """Generate an SEO-optimized caption for this photograph.
Include relevant keywords naturally that would help with search discovery.
Focus on describing the scene, subjects, and context.
Make it descriptive but readable (2-3 sentences).""",
    CaptionStyle.SOCIAL_MEDIA: """Generate an engaging social media caption for this photograph.
The caption should be attention-grabbing and shareable.
Include relevant hashtags at the end.
Keep it concise and memorable.""",
}

# Event detection prompt
EVENT_DETECTION_PROMPT = """Analyze this photograph and identify:
1. Event type (wedding, portrait, landscape, corporate, product, etc.)
2. Setting (indoor, outdoor, studio, etc.)
3. Key subjects or elements
4. Mood/atmosphere
5. Season/time of day if detectable

Respond in JSON format:
{
    "event_type": "...",
    "setting": "...",
    "subjects": ["..."],
    "mood": "...",
    "time_context": "...",
    "keywords": ["..."]
}"""


class CaptionService:
    """
    AI-powered caption generation service.

    Features:
    - Multiple caption styles (professional, casual, SEO, social media)
    - Event context detection for better captions
    - Regeneration support
    - Gemini LLM integration
    """

    async def generate_captions(
        self,
        db: AsyncSession,
        asset_id: UUID,
        workspace_id: UUID,
        image_description: Optional[str] = None,
        styles: Optional[list[CaptionStyle]] = None,
    ) -> Caption:
        """
        Generate caption suggestions for a photo.

        Args:
            db: Database session
            asset_id: Asset ID
            workspace_id: Workspace ID
            image_description: Optional image description for context
            styles: List of styles to generate (defaults to all)

        Returns:
            Caption object with suggestions
        """
        if styles is None:
            styles = list(CaptionStyle)

        logger.info(
            "Generating captions",
            asset_id=str(asset_id),
            styles=[s.value for s in styles],
        )

        # Check for existing caption
        existing = await self.get_caption(db, asset_id, workspace_id)

        # Detect event context if we have image description
        detected_context = None
        if image_description:
            detected_context = await self._detect_event_context(image_description)

        # Generate captions for each style
        suggestions = []
        for style in styles:
            caption_text = await self._generate_single_caption(
                style=style,
                image_description=image_description,
                context=detected_context,
            )

            if caption_text:
                suggestions.append(
                    {
                        "text": caption_text,
                        "style": style.value,
                        "score": 1.0,  # Could add scoring logic
                    }
                )

        if existing:
            # Update existing caption
            existing.suggestions = suggestions
            existing.detected_context = detected_context
            await db.flush()
            await db.refresh(existing)
            return existing

        # Create new caption
        caption = Caption(
            asset_id=asset_id,
            workspace_id=workspace_id,
            suggestions=suggestions,
            detected_context=detected_context,
            model_name=settings.GEMINI_MODEL,
        )

        db.add(caption)
        await db.flush()
        await db.refresh(caption)

        logger.info(
            "Captions generated",
            asset_id=str(asset_id),
            count=len(suggestions),
        )

        return caption

    async def regenerate_caption(
        self,
        db: AsyncSession,
        asset_id: UUID,
        workspace_id: UUID,
        style: CaptionStyle,
        image_description: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Regenerate a single caption style.

        Args:
            db: Database session
            asset_id: Asset ID
            workspace_id: Workspace ID
            style: Caption style to regenerate
            image_description: Optional image description

        Returns:
            New caption suggestion dict
        """
        caption = await self.get_caption(db, asset_id, workspace_id)
        if not caption:
            return None

        # Generate new caption
        new_text = await self._generate_single_caption(
            style=style,
            image_description=image_description,
            context=caption.detected_context,
        )

        if not new_text:
            return None

        new_suggestion = {
            "text": new_text,
            "style": style.value,
            "score": 1.0,
        }

        # Replace existing suggestion for this style or append
        updated = False
        for i, s in enumerate(caption.suggestions):
            if s.get("style") == style.value:
                caption.suggestions[i] = new_suggestion
                updated = True
                break

        if not updated:
            caption.suggestions.append(new_suggestion)

        await db.flush()

        logger.info(
            "Caption regenerated",
            asset_id=str(asset_id),
            style=style.value,
        )

        return new_suggestion

    async def get_caption(
        self,
        db: AsyncSession,
        asset_id: UUID,
        workspace_id: UUID,
    ) -> Optional[Caption]:
        """Get existing caption for an asset."""
        result = await db.execute(
            select(Caption)
            .where(Caption.asset_id == asset_id)
            .where(Caption.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def select_caption(
        self,
        db: AsyncSession,
        asset_id: UUID,
        workspace_id: UUID,
        caption_text: str,
    ) -> bool:
        """
        Mark a caption as selected by the user.

        Args:
            db: Database session
            asset_id: Asset ID
            workspace_id: Workspace ID
            caption_text: Selected caption text

        Returns:
            True if successful
        """
        caption = await self.get_caption(db, asset_id, workspace_id)
        if not caption:
            return False

        caption.selected_caption = caption_text
        await db.flush()

        logger.info("Caption selected", asset_id=str(asset_id))
        return True

    async def _detect_event_context(
        self,
        image_description: str,
    ) -> Optional[dict]:
        """
        Detect event context from image description.

        Args:
            image_description: Description of the image

        Returns:
            Detected context dict
        """
        try:
            prompt = f"""Based on this image description, {EVENT_DETECTION_PROMPT}

Image description: {image_description}"""

            response = await generate_text(prompt)

            if response:
                # Try to parse as JSON
                import json

                try:
                    # Find JSON in response
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    if start >= 0 and end > start:
                        return json.loads(response[start:end])
                except json.JSONDecodeError:
                    pass

            return None

        except Exception as e:
            logger.warning("Event detection failed", error=str(e))
            return None

    async def _generate_single_caption(
        self,
        style: CaptionStyle,
        image_description: Optional[str],
        context: Optional[dict],
    ) -> Optional[str]:
        """
        Generate a single caption in a specific style.

        Args:
            style: Caption style
            image_description: Image description
            context: Detected event context

        Returns:
            Generated caption text
        """
        try:
            # Build prompt
            prompt_parts = [CAPTION_PROMPTS[style]]

            if image_description:
                prompt_parts.append(f"\nImage description: {image_description}")

            if context:
                context_str = []
                if context.get("event_type"):
                    context_str.append(f"Event type: {context['event_type']}")
                if context.get("mood"):
                    context_str.append(f"Mood: {context['mood']}")
                if context.get("subjects"):
                    context_str.append(f"Subjects: {', '.join(context['subjects'])}")

                if context_str:
                    prompt_parts.append(f"\nContext: {'; '.join(context_str)}")

            prompt_parts.append("\nCaption:")

            prompt = "\n".join(prompt_parts)

            response = await generate_text(prompt)

            if response:
                # Clean up the response
                caption = response.strip()
                # Remove any leading "Caption:" if present
                if caption.lower().startswith("caption:"):
                    caption = caption[8:].strip()
                return caption

            return None

        except Exception as e:
            logger.error(
                "Caption generation failed",
                style=style.value,
                error=str(e),
            )
            return None


# Global service instance
caption_service = CaptionService()
