FROM python:3.11-slim as base

# Metadata
LABEL maintainer="Ultimate AI CLI Agent Contributors"
LABEL description="The Ultimate AI CLI Agent with internet access, browser automation, and server management"
LABEL version="2.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Basic utilities
    wget \
    curl \
    git \
    unzip \
    # For Chrome/Selenium
    gnupg \
    lsb-release \
    # Build tools (may be needed for some packages)
    build-essential \
    # Network tools
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome for Selenium support
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copy the entire project
COPY . .

# Install the package in development mode
RUN pip install -e .[full]

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash agent \
    && chown -R agent:agent /app

# Switch to non-root user
USER agent

# Create directories for user data
RUN mkdir -p /app/data /app/logs /app/downloads

# Set up environment for the agent
ENV AGENT_DATA_DIR=/app/data
ENV AGENT_LOG_DIR=/app/logs
ENV AGENT_DOWNLOAD_DIR=/app/downloads

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ultimate-ai-cli --version || exit 1

# Default command
ENTRYPOINT ["ultimate-ai-cli"]
CMD ["--help"]

# Multi-stage build for different variants
FROM base as minimal
RUN pip uninstall -y selenium beautifulsoup4 flask fastapi pandas numpy

FROM base as web
# Web-focused variant with all web tools
RUN echo "Web variant with full browser automation support"

FROM base as server
# Server-focused variant
RUN echo "Server variant with process management tools"

FROM base as full
# Full variant (default)
RUN echo "Full variant with all features enabled"
