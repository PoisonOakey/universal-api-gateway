# ─────────────────────────────────────────────
#  Stage 1: Lightweight Python image
# ─────────────────────────────────────────────
FROM python:3.12-slim

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
COPY main.py .
COPY api/ ./api/

# ─────────────────────────────────────────────
#  Expose port and start the server
# ─────────────────────────────────────────────
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
