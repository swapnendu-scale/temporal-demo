# Start the Temporal dev server (run in a separate terminal)
server:
	temporal server start-dev

# Run the broken version of the demo
broken: _ensure-server
	@echo "🍕 Setting up BROKEN demo..."
	git checkout a5d25c7 -- demo/workflows.py demo/activities.py
	-@git reset HEAD demo/workflows.py demo/activities.py >/dev/null 2>&1
	@cd demo && rm -f charges.txt
	@echo "🚀 Starting backend (FastAPI + Worker) and frontend..."
	@bash -c 'trap "kill 0" EXIT; cd demo && uv run api.py & cd demo/frontend && npm run dev & wait'

# Run the fixed version of the demo
fixed: _ensure-server
	@echo "🍕 Setting up FIXED demo..."
	git checkout 2efa1d4 -- demo/workflows.py demo/activities.py
	-@git reset HEAD demo/workflows.py demo/activities.py >/dev/null 2>&1
	@cd demo && rm -f charges.txt
	@echo "🚀 Starting backend (FastAPI + Worker) and frontend..."
	@bash -c 'trap "kill 0" EXIT; cd demo && uv run api.py & cd demo/frontend && npm run dev & wait'

# Run just the backend (FastAPI + Temporal worker)
backend: _ensure-server
	cd demo && uv run api.py

# Run just the frontend
frontend:
	cd demo/frontend && npm run dev

[private]
_ensure-server:
	@bash -c 'if ! nc -z localhost 7233 2>/dev/null; then echo "❌ Temporal server is not running. Start it first with: just server"; exit 1; fi'
