# Base image: Debian with Python 3.12 preinstalled (slim = smaller size)
FROM python:3.12-slim

# Print logs immediately (no buffering) so "docker logs" shows them live
ENV PYTHONUNBUFFERED=1
# Do not write .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Install the C compiler and the MariaDB client library needed to build the
# "mariadb" Python package, then delete the apt cache to keep the image small
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a system user without a home folder: the app must not run as root
RUN useradd --system --no-create-home app

# Set the working directory (created if missing)
WORKDIR /app

# Give the app user write access to /app (weather.json is written there)
RUN chown app:app /app

# Copy only requirements.txt first so Docker caches the pip layer
# as long as the dependencies do not change
COPY requirements.txt .

# Install the Python dependencies without keeping pip's download cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project (.dockerignore excludes .env, .git, ...)
COPY --chown=app:app . .

# From now on, every command (and the container itself) runs as "app"
USER app

# Document the ports used: 5000 = web server, 4000 = TCP listener
# (the real publishing is done in docker-compose.yml)
EXPOSE 5000 4000

# Start the project (web server + TCP listener); the list form lets
# Python receive the stop signal from "docker stop"
CMD ["python", "main.py"]
 