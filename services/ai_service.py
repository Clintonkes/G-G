import logging

import httpx

from core.config import settings


logger = logging.getLogger("gghomes.ai")


async def generate_listing_summary(title: str, description: str, amenities: list[str]) -> str:
    if not settings.openai_api_key:
        return description

    payload = {
        "model": settings.openai_model,
        "messages": [
            {
                "role": "system",
                "content": "You write concise, trustworthy Nigerian real-estate listing copy for a rental marketplace.",
            },
            {
                "role": "user",
                "content": f"Title: {title}\nAmenities: {', '.join(amenities)}\nDescription: {description}\n\nRewrite this as polished listing copy in under 120 words.",
            },
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("OpenAI listing summary failed — using original description. Reason: %s", exc)
        return description


async def validate_property_image(url: str) -> bool:
    """Return True if the image shows a building/room/property, False otherwise.

    Skips validation silently if OpenAI is not configured or if the API is
    unreachable — uploads should never be blocked by a missing AI key.
    """
    if not settings.openai_api_key:
        return True

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_model,
                    "max_tokens": 5,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": url, "detail": "low"},
                                },
                                {
                                    "type": "text",
                                    "text": (
                                        "Is this image a photograph of a building, house, apartment, room, "
                                        "office, warehouse, or any real estate property interior or exterior? "
                                        "Reply with only YES or NO."
                                    ),
                                },
                            ],
                        }
                    ],
                },
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"].strip().upper()
            return answer.startswith("YES")
    except Exception as exc:
        logger.warning("Image validation check failed — allowing upload. Reason: %s", exc)
        return True
