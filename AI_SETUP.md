# AI Setup

Yes, the AI layer has a clear place in this platform.

Current backend support:

- `app/services/ai_service.py` is already wired to call OpenAI when keys are present.
- `app/api/routes/properties.py` uses that service to polish listing descriptions during property creation.

Good next AI use cases for this project:

- Listing description cleanup for landlords
- Smarter property search ranking and natural-language search
- Tenant support assistant that preserves the original WhatsApp-style guidance
- Admin copilot for verification summaries and appointment follow-ups

To enable it, copy these variables into `G-G/.env`:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_EMBEDDING_MODEL`

Recommended note:

- Keep OpenAI keys only in the backend repo (`G-G`), not the frontend repo (`G-G-Homes`).
