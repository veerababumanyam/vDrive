"""Gemini LLM client initialization and utilities."""

from typing import Optional, Any
import structlog

from .config import settings

logger = structlog.get_logger()

# Global Gemini client
_gemini_model = None


def init_gemini() -> bool:
    """
    Initialize Gemini client.

    Returns:
        True if successfully initialized, False otherwise
    """
    global _gemini_model

    if not settings.gemini_enabled:
        logger.warning("Gemini API key not configured, LLM features disabled")
        return False

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "max_output_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
                "temperature": settings.GEMINI_TEMPERATURE,
            },
        )
        logger.info("Gemini client initialized", model=settings.GEMINI_MODEL)
        return True
    except Exception as e:
        logger.error("Failed to initialize Gemini client", error=str(e))
        return False


def get_gemini_model():
    """Get the initialized Gemini model."""
    if _gemini_model is None:
        init_gemini()
    return _gemini_model


async def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Optional[str]:
    """
    Generate text using Gemini.

    Args:
        prompt: The prompt to send to the model
        system_instruction: Optional system instruction
        max_tokens: Override max output tokens
        temperature: Override temperature

    Returns:
        Generated text or None if failed
    """
    model = get_gemini_model()
    if model is None:
        logger.error("Gemini model not initialized")
        return None

    try:
        import google.generativeai as genai

        # Build generation config with overrides
        generation_config = {}
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        if temperature is not None:
            generation_config["temperature"] = temperature

        # Create model with system instruction if provided
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=system_instruction,
                generation_config=generation_config or None,
            )

        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config if generation_config else None,
        )

        if response.text:
            return response.text
        return None
    except Exception as e:
        logger.error("Gemini generation failed", error=str(e))
        return None


async def generate_chat_response(
    messages: list[dict[str, str]],
    system_instruction: Optional[str] = None,
) -> Optional[str]:
    """
    Generate a chat response using Gemini.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        system_instruction: Optional system instruction for context

    Returns:
        Generated response or None if failed
    """
    model = get_gemini_model()
    if model is None:
        logger.error("Gemini model not initialized")
        return None

    try:
        import google.generativeai as genai

        # Create model with system instruction
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=system_instruction,
            )

        # Convert messages to Gemini format
        chat = model.start_chat(history=[])

        # Process all but the last message as history
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            chat.history.append({
                "role": role,
                "parts": [msg["content"]],
            })

        # Send the last message and get response
        last_message = messages[-1]["content"]
        response = await chat.send_message_async(last_message)

        if response.text:
            return response.text
        return None
    except Exception as e:
        logger.error("Gemini chat generation failed", error=str(e))
        return None


def close_gemini() -> None:
    """Cleanup Gemini resources."""
    global _gemini_model
    _gemini_model = None
    logger.info("Gemini client closed")
