from collections.abc import Sequence

import httpx

from core.config import settings


async def send_email(to: Sequence[str], subject: str, html: str) -> None:
    if not settings.resend_api_key:
        return

    async with httpx.AsyncClient(timeout=20) as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={"from": settings.email_from, "to": list(to), "subject": subject, "html": html},
        )
