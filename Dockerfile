# ====================================================================
# Base Image
# ====================================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files & force unbuffered logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ====================================================================
# System Packages
# ====================================================================
# Install essential system libraries:
# - build-essential: needed if C extensions compile
# - libxml2 / libxslt: needed for BeautifulSoup + lxml acceleration
# - ca-certificates: critical for OpenAI + WordPress HTTPS
# - curl: useful for debugging inside container
# ====================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2 \
    libxslt1.1 \
    libxslt1-dev \
    libxml2-dev \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ====================================================================
# Workdir & Code Copy
# ====================================================================
WORKDIR /app
COPY . /app

# ====================================================================
# Python Dependencies
# ====================================================================
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# ====================================================================
# Optional: Timezone (if your cron depends on times)
# ====================================================================
#ENV TZ=America/New_York

# ====================================================================
# Entrypoint
# ====================================================================
