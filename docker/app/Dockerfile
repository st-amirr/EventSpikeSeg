FROM python:3.11-slim-bookworm

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ghdl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/eventscnn
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu torch==2.2.2 \
    && python -m pip install --no-cache-dir '.[dev,rtl]'

WORKDIR /workspace
