FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -i https://pypi.org/simple/ -r requirements.txt
COPY frontend/ frontend/
COPY backend/ backend/
EXPOSE 8501
CMD ["streamlit", "run", "frontend/dashboard/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]