# ─────────────────────────────────────────────
#  Stage 1: Lightweight Python image
# ─────────────────────────────────────────────
FROM python:3.12-slim

# Links the published package back to this repository. Without it GHCR treats
# the image as unattached: it never appears under Packages on the repo page,
# and its own page does not say where it came from.
LABEL org.opencontainers.image.source="https://github.com/PoisonOakey/universal-api-gateway"

# Create a non-root user
RUN useradd -m -u 1000 gateway_user

# ─────────────────────────────────────────────
#  Set working directory inside the container
# ─────────────────────────────────────────────
WORKDIR /app

# ─────────────────────────────────────────────
#  Install dependencies first (cached layer)
# ─────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────
#  Copy only the API source code we wrote
# ─────────────────────────────────────────────
COPY src/ .

# Ensure the non-root user owns the app directory
RUN chown -R gateway_user:gateway_user /app

# Switch to non-root user
USER 1000

# ─────────────────────────────────────────────
#  Expose port and start the server
# ─────────────────────────────────────────────
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
