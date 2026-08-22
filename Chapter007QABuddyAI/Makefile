# ============================================================
# QABuddy.ai — Developer Makefile
# Convenience commands for local development and CI
# ============================================================

.PHONY: help setup start-db stop-db ingest run-api run-ui test test-unit test-integration clean docker-up docker-down

# ─── Default: show help ──────────────────────────────────────

help:
	@echo ""
	@echo "  QABuddy.ai — Development Commands"
	@echo "  =================================="
	@echo ""
	@echo "  Setup:"
	@echo "    make setup          Install Python dependencies"
	@echo "    make clone-repos    Clone Selenium + Playwright repos into data/"
	@echo ""
	@echo "  Database:"
	@echo "    make start-db       Start Qdrant vector database (Docker)"
	@echo "    make stop-db        Stop Qdrant"
	@echo ""
	@echo "  Ingestion:"
	@echo "    make ingest         Ingest all data sources"
	@echo "    make ingest-dry     Dry run (parse + chunk, no embedding)"
	@echo "    make test-retrieval Run retrieval quality tests"
	@echo ""
	@echo "  Running:"
	@echo "    make run-api        Start the FastAPI backend (port 8000)"
	@echo "    make run-ui         Start the Streamlit UI (port 8501)"
	@echo ""
	@echo "  Testing:"
	@echo "    make test           Run all unit tests"
	@echo "    make test-unit      Run unit tests only (no external deps)"
	@echo "    make test-cov       Run tests with coverage report"
	@echo ""
	@echo "  Docker:"
	@echo "    make docker-up      Start full stack via Docker Compose"
	@echo "    make docker-down    Stop Docker Compose stack"
	@echo ""
	@echo "  Cleanup:"
	@echo "    make clean          Remove __pycache__ and .pytest_cache"
	@echo ""

# ─── Setup ───────────────────────────────────────────────────

setup:
	pip install -r requirements.txt

clone-repos:
	python scripts/clone_repos.py

# ─── Database ────────────────────────────────────────────────

start-db:
	docker run -d --name qdrant-qabuddy \
		-p 6333:6333 \
		-v qdrant_storage:/qdrant/storage \
		qdrant/qdrant
	@echo "✅ Qdrant started at http://localhost:6333"
	@echo "   Dashboard: http://localhost:6333/dashboard"

stop-db:
	docker stop qdrant-qabuddy && docker rm qdrant-qabuddy
	@echo "🛑 Qdrant stopped"

# ─── Ingestion ───────────────────────────────────────────────

ingest:
	python scripts/ingest_all.py

ingest-recreate:
	python scripts/ingest_all.py --recreate

ingest-dry:
	python scripts/ingest_all.py --dry-run

test-retrieval:
	python scripts/test_retrieval.py

# ─── Running ─────────────────────────────────────────────────

run-api:
	python -m src.api.main

run-ui:
	streamlit run src/ui/app.py

# ─── Testing ─────────────────────────────────────────────────

test:
	python -m pytest tests/ -v

test-unit:
	python -m pytest tests/ -v -m "not integration and not slow"

test-cov:
	python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# ─── Docker ──────────────────────────────────────────────────

docker-up:
	cd docker && docker compose up -d --build
	@echo "✅ QABuddy.ai stack started"
	@echo "   Chat UI:  http://localhost:8501"
	@echo "   API:      http://localhost:8000/docs"
	@echo "   Qdrant:   http://localhost:6333/dashboard"

docker-down:
	cd docker && docker compose down

# ─── Cleanup ─────────────────────────────────────────────────

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	@echo "🧹 Cleaned up"
