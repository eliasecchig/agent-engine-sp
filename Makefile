test:
	uv run pytest tests/unit && uv run pytest tests/integration

playground:
	PYTHONPATH=. uv run streamlit run frontend/streamlit_app.py --browser.serverAddress=localhost --server.enableCORS=false --server.enableXsrfProtection=false

backend:
	uv run app/agent_engine_app.py

lint:
	uv run codespell
	uv run flake8 .
	uv run pylint .
	uv run mypy .
	uv run black .
