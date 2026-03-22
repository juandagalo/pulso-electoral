FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml .python-version ./

# Install Python dependencies
RUN uv sync --all-groups

# Download spaCy model
RUN uv run python -m spacy download es_core_news_lg

# Copy project code
COPY . .

# Default: run the Streamlit app
EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
