# Start the Temporal dev server (run in a separate terminal)
server:
	temporal server start-dev

# Run the broken version of the demo (requires `just server` in another terminal)
broken: _ensure-server
	@echo "🍕 Setting up broken demo..."
	git checkout 03b0038 -- demo/workflows.py demo/activities.py
	-@git reset HEAD demo/workflows.py demo/activities.py >/dev/null 2>&1
	@cd demo && rm -f charges.txt
	@echo "🚀 Starting Temporal worker and triggering workflow..."
	@bash -c 'trap "kill 0" EXIT; cd demo && uv run worker.py & sleep 2 && cd demo && uv run starter.py && echo "⏳ Worker is running. Press Ctrl+C to stop." && wait'

# Run the fixed version of the demo (requires `just server` in another terminal)
fixed: _ensure-server
	@echo "🍕 Setting up fixed demo..."
	git checkout 8529623 -- demo/workflows.py demo/activities.py
	-@git reset HEAD demo/workflows.py demo/activities.py >/dev/null 2>&1
	@cd demo && rm -f charges.txt
	@echo "🚀 Starting Temporal worker and triggering workflow..."
	@bash -c 'trap "kill 0" EXIT; cd demo && uv run worker.py & sleep 2 && cd demo && uv run starter.py && echo "⏳ Worker is running. Press Ctrl+C to stop." && wait'

[private]
_ensure-server:
	@bash -c 'if ! nc -z localhost 7233 2>/dev/null; then echo "❌ Temporal server is not running. Start it first with: just server"; exit 1; fi'
