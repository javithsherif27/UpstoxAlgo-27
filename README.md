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

### Quick Start (Recommended)

**Option 1: Full Stack with LocalStack (Best for development)**
```bash
# One command to start everything
dev-launcher.bat

# Or directly:
start-local.bat
```
This starts LocalStack + Backend + Frontend with local AWS services.

**Option 2: Individual Services**
```bash
# Just LocalStack
start-localstack.bat

# Backend only (auto-detects LocalStack)
start-backend.bat  

# Frontend only
start-frontend.bat
```

### Environment Setup

1. **Install Dependencies**
```bash
# Backend (Python 3.13.7 assumed)
pip install -r backend/requirements.txt

# Frontend
cd frontend && npm install
```

2. **Environment Configuration**
- `.env.local` - LocalStack development (auto-created)
- `.env.production` - Production AWS (template provided)
- LocalStack runs AWS services locally at no cost

3. **Available Services**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000  
- LocalStack: http://localhost:4566
- DynamoDB Admin: http://localhost:8001

### LocalStack Benefits
- ✅ No AWS costs during development
- ✅ Offline development capability  
- ✅ Fast iteration cycles
- ✅ Production parity with real AWS APIs
- ✅ Team environment consistency

See [LOCALSTACK.md](LOCALSTACK.md) for detailed setup and troubleshooting.

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
