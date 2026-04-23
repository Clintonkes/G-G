import httpx

from core.config import settings


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
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
