PYTHON ?= python3

.PHONY: install migrate seed run-api run-ui test lint format demo scheduler

install:
	$(PYTHON) -m pip install -e .[dev]

migrate:
	alembic upgrade head

seed:
	$(PYTHON) scripts/seed_demo_data.py --demo-only

run-api:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-ui:
	streamlit run app/ui/streamlit_app.py --server.port 8501

test:
	pytest

lint:
	ruff check app scripts tests

format:
	ruff format app scripts tests

demo:
	$(PYTHON) scripts/demo_chat.py

scheduler:
	$(PYTHON) scripts/run_scheduler.py --demo-only
