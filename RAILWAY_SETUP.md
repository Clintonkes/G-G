# Railway Setup

The signup error you saw:

`POST http://localhost:8000/api/auth/register net::ERR_CONNECTION_REFUSED`

happens because the frontend falls back to `http://localhost:8000` when `NEXT_PUBLIC_API_URL` is not set. That means the frontend is live, but no reachable backend is configured for it.

## 1. Deploy the backend service (`G-G`)

Create a new Railway service from the `G-G` repo/folder.

Use these environment variables:

- `DATABASE_URL`
- `SECRET_KEY`
- `FRONTEND_URL`
- `CORS_ORIGINS`
- Any optional provider keys you want to enable later (`FLUTTERWAVE_*`, `CLOUDINARY_*`, `RESEND_API_KEY`, `OPENAI_*`, `GOOGLE_MAPS_API_KEY`)

Minimum working example:

```env
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql://postgres:password@host:5432/railway
SECRET_KEY=replace-with-a-long-random-secret
FRONTEND_URL=https://your-frontend-domain.up.railway.app
CORS_ORIGINS=https://your-frontend-domain.up.railway.app,http://localhost:3000
ACCESS_TOKEN_EXPIRE_MINUTES=10080
ADMIN_EMAIL=admin@gandghomesltd.org
ADMIN_PASSWORD=ChangeMe123!
```

The backend now includes a `Dockerfile`, so Railway can build it directly.

After deploy, open:

- `https://your-backend-domain.up.railway.app/api/health`

It should return:

```json
{"status":"ok","app":"G&G Homes API"}
```

## 2. Deploy the frontend service (`G-G-Homes`)

Create a separate Railway service from the `G-G-Homes` repo/folder.

Set:

```env
NEXT_PUBLIC_API_URL=https://your-backend-domain.up.railway.app
NEXT_PUBLIC_APP_URL=https://your-frontend-domain.up.railway.app
```

Optional frontend keys:

- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`
- `NEXT_PUBLIC_FLUTTERWAVE_PUBLIC_KEY`

## 3. Confirm frontend-backend connection

Once both services are deployed:

1. Open the frontend URL.
2. Open DevTools.
3. Submit the signup form.
4. Confirm the request goes to:
   `https://your-backend-domain.up.railway.app/api/auth/register`
   not `http://localhost:8000/api/auth/register`

## 4. Local development

Backend:

```bash
cd /home/emeka/G-G
cp .env.example .env
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd /home/emeka/G-G-Homes
cp .env.example .env.local
npm install
npm run dev
```

For local frontend work, keep:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 5. Most likely cause of your current error

Your frontend service is deployed, but `NEXT_PUBLIC_API_URL` is either missing or still pointing to the default local fallback. Because of that, the browser tries to call `http://localhost:8000`, which only works when your backend is running locally on your machine.
