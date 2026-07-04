# PCB defect detection — one image serves both the FastAPI backend (default CMD)
# and the Streamlit UI (compose overrides the command).
FROM python:3.11-slim

# opencv (pulled in by ultralytics) needs these shared libs on slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only torch first: the default PyPI wheels bundle CUDA (~2.5 GB heavier)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY app/ app/
COPY .streamlit/ .streamlit/
COPY models/best.pt models/best.pt

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PCB_DEVICE=cpu

EXPOSE 8000 8501

# API by default; docker-compose.yml overrides this for the ui service
CMD ["uvicorn", "pcb_vision.api:app", "--host", "0.0.0.0", "--port", "8000"]
