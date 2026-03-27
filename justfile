# Start the Temporal dev server (run in a separate terminal)
server:
	temporal server start-dev

# Run the demo (Pizza Delivery App)
demo: _ensure-server
	@cd demo && rm -f charges.txt
	@echo "🍕 Starting backend (FastAPI + Worker) and frontend..."
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
