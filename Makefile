.PHONY: help install_env test test_verbose test_coverage check lint docs docs_test clean_env download_models collect_rss collect_reddit collect_gdelt_acled collect_all analyze export run_app

####----Basic configurations----####

install_env: ## Install libs with UV and pre-commit
	@echo "Creating virtual environment using UV"
	uv sync --all-groups
	@echo "Installing pre-commit..."
	uv run pre-commit install
	@echo "Activate virtual environment..."
	@bash -c "source .venv/bin/activate"

init_git: ## Initialize git repository
	@echo "Initializing local git repository..."
	git init -b main
	git add .
	git commit -m "feat: initial project scaffold for Pulso Electoral Colombia 2026"
	@echo "Local Git already set!"

####----Models----####

download_models: ## Download spaCy Spanish model
	@echo "Downloading spaCy es_core_news_lg..."
	uv run python -m spacy download es_core_news_lg
	@echo "Models ready!"

####----Data Collection----####

collect_rss: ## Run RSS collection notebook
	@echo "Collecting RSS feeds..."
	uv run jupyter execute notebooks/1-data/01_mgo_rss_collection_20260322.ipynb

collect_reddit: ## Run Reddit collection notebook
	@echo "Collecting Reddit posts..."
	uv run jupyter execute notebooks/1-data/02_mgo_reddit_collection_20260322.ipynb

collect_gdelt_acled: ## Run GDELT + ACLED collection notebook
	@echo "Collecting GDELT and ACLED data..."
	uv run jupyter execute notebooks/1-data/03_mgo_gdelt_acled_collection_20260323.ipynb

collect_all: collect_rss collect_reddit collect_gdelt_acled ## Run all collection notebooks

####----Analysis----####

analyze: ## Run all analysis notebooks
	@echo "Running analysis notebooks..."
	uv run jupyter execute notebooks/3-analysis/01_mgo_sentiment_analysis_20260324.ipynb
	uv run jupyter execute notebooks/3-analysis/02_mgo_entity_extraction_20260325.ipynb
	uv run jupyter execute notebooks/3-analysis/03_mgo_narrative_topics_20260325.ipynb

####----Output----####

export: ## Run output notebooks (dataset export + analysis summary)
	@echo "Running output notebooks..."
	uv run jupyter execute notebooks/4-output/01_mgo_dataset_export_20260327.ipynb
	uv run jupyter execute notebooks/4-output/02_mgo_analysis_summary_20260327.ipynb

####----App----####

run_app: ## Start Streamlit dashboard
	@echo "Starting Streamlit dashboard..."
	uv run streamlit run app/app.py

####----Tests----####

test: ## Test the code with pytest and coverage
	@echo "Testing code: Running pytest"
	@uv run pytest --cov

test_verbose: ## Test the code with pytest and coverage in verbose mode
	@echo "Testing code: Running pytest in verbose mode"
	@uv run pytest --no-header -v --cov

test_coverage: ## Test coverage report coverage.xml
	@echo "Testing code: Running pytest with coverage"
	@uv run pytest --cov --cov-report xml:coverage.xml

####----Pre-commit----####

pre-commit_update: ## Update pre-commit hooks
	@echo "Updating pre-commit hooks..."
	uv run pre-commit clean
	uv run pre-commit autoupdate

####----Docs----####

docs: ## Build and serve the documentation
	@echo "Viewing documentation..."
	uv run mkdocs serve

docs_test: ## Test if documentation can be built without warnings or errors
	@uv run mkdocs build -s

####----Clean----####

clean_env: ## Clean .venv virtual environment
	@echo "Cleaning the environment..."
	@[ -d .venv ] && rm -rf .venv || echo ".venv directory does not exist"

clean: ## Remove caches, compiled files, DB files
	@echo "Cleaning caches and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.db" -delete 2>/dev/null || true

####----Git----####

switch_main: ## Switch to main branch and pull
	@echo "Switching to main branch..."
	@git switch main
	@git pull

####----Checks----####

check: ## Run code quality tools with pre-commit hooks
	@echo "Linting, formatting and static type checking code: Running pre-commit"
	@uv run pre-commit run -a

lint: ## Run ruff only
	@echo "Linting code: Running ruff"
	@uv run pre-commit run ruff

####----Project----####

help:
	@printf "%-30s %s\n" "Target" "Description"
	@printf "%-30s %s\n" "-----------------------" "----------------------------------------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
