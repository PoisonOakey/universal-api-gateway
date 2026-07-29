# ─────────────────────────────────────────────
#  Stage 1: Lightweight Python image
# ─────────────────────────────────────────────
FROM python:3.12.4-slim

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
