# Algo Trading App

Full-stack demo integrating with Upstox Open API.

## Stack
- Frontend: React + TypeScript + Vite + TailwindCSS + React Query + React Router
- Backend: FastAPI (Python 3.13) on AWS Lambda via SAM + Mangum
- Cache: DynamoDB daily instruments cache
- Storage: S3 static site hosting

## Features
- Login with Upstox user id + manual access token (token stored only client-side until EOD IST)
- JWT session cookie (HttpOnly) for backend auth
- Dashboard shows profile
- Instruments list cached daily
- Modular tab system (Dashboard, Instruments, Strategies placeholder)

## Security Notes
- Upstox token never persisted on server
- Cookies are HttpOnly, Secure, SameSite=Lax
- CORS restricted via env `ALLOWED_ORIGIN`
- Tokens masked in logs

## Local Development

Copy `.env.example` to `.env` and set values.

Install backend deps (Python 3.13.7 assumed):
```
pip install -r backend/requirements.txt
```
Install frontend deps:
```
cd frontend && npm install
```
Run concurrently (or use make):
```
make dev
```
Backend will run at `http://127.0.0.1:8000` by uvicorn and frontend at `http://localhost:5173`.

## EOD Token Expiry
Client stores token with `expiresAt` set to 23:59:59 IST of current day. On load or API call if expired it is cleared and user redirected to `/login`.

## Deployment (SAM)
```
cd infra
sam build
sam deploy --guided
```
Provide `AppJwtSecret` parameter (strong secret) and allowed origin (your deployed frontend URL).
Upload frontend build to the created S3 bucket:
```
cd frontend
npm run build
aws s3 sync dist/ s3://<bucket-name>/ --delete
```

## API Endpoints
- POST `/api/session/login` { user_id } -> sets cookie
- POST `/api/session/logout`
- GET `/api/upstox/profile` (requires cookie + `X-Upstox-Access-Token` header)
- GET `/api/instruments?refresh=false`

## How to Obtain Upstox Token
Follow Upstox documentation to authenticate and retrieve an access token. Paste it into the login form. Token is only stored locally.

## Tests
Backend: `pytest backend/tests`
Frontend: `cd frontend && npm test`

## Future Enhancements
- CloudFront distribution in front of S3
- Rate limiting at API Gateway stage usage plan
- Feature flags infra
- Skeleton loaders & optimistic updates
- Additional Upstox endpoints (orders, positions)

## License
MIT
