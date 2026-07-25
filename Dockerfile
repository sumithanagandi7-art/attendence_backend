# SmartGov Attendance backend — production container
FROM python:3.11-slim

# System dependencies required to build dlib (face_recognition's engine)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching on rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn psycopg2-binary

# Copy the rest of the application
COPY . .

# Persistent-ish local dir for uploaded face photos (see deployment README
# for why this needs a real persistent disk or object storage in production)
RUN mkdir -p /app/uploads/faces

EXPOSE 5000

# gunicorn: production-grade WSGI server (Flask's built-in dev server is not
# safe/performant for real traffic). 2 workers is a safe default for a free-tier
# instance; increase once you know your real traffic and server size.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
