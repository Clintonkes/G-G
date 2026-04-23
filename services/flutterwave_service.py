from datetime import date

import httpx

from core.config import settings


async def initialize_flutterwave_payment(
    email: str,
    name: str,
    amount: float,
    tx_ref: str,
    redirect_url: str,
    title: str,
    description: str,
    property_id: str | None = None,
    tenancy_start_date: date | None = None,
    tenancy_end_date: date | None = None,
) -> str:
    if not settings.flutterwave_secret_key:
        return f"{settings.frontend_url}/payments/mock-success?tx_ref={tx_ref}"

    payload = {
        "tx_ref": tx_ref,
        "amount": amount,
        "currency": "NGN",
        "redirect_url": redirect_url,
        "customer": {"email": email, "name": name},
        "customizations": {"title": title, "description": description},
        "meta": {
            "property_id": property_id,
            "tenancy_start_date": tenancy_start_date.isoformat() if tenancy_start_date else None,
            "tenancy_end_date": tenancy_end_date.isoformat() if tenancy_end_date else None,
        },
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.flutterwave.com/v3/payments",
            headers={"Authorization": f"Bearer {settings.flutterwave_secret_key}"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"]["link"]


async def verify_flutterwave_payment(tx_ref: str, transaction_id: str | None = None) -> dict:
    if not settings.flutterwave_secret_key:
        return {"status": "successful", "tx_ref": tx_ref, "id": transaction_id or "mock"}

    target = (
        f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        if transaction_id
        else f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={tx_ref}"
    )
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(target, headers={"Authorization": f"Bearer {settings.flutterwave_secret_key}"})
        response.raise_for_status()
        return response.json().get("data", {})
