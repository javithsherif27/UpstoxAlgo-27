PY=python
FRONTEND_DIR=frontend
BACKEND_DIR=backend

.PHONY: dev backend frontend deploy

dev:
	cd $(BACKEND_DIR) && uvicorn app:app --reload & \
	cd $(FRONTEND_DIR) && npm run dev

frontend-build:
	cd $(FRONTEND_DIR) && npm ci && npm run build

backend-deps:
	cd $(BACKEND_DIR) && pip install -r requirements.txt -t ./.venv-packages

sam-build:
	cd infra && sam build

sam-deploy:
	cd infra && sam deploy --guided

deploy: frontend-build sam-build sam-deploy
