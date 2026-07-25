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

# ── KEY FIX: compile dlib with a SINGLE thread ──────────────────────────
# dlib's cmake build defaults to using all CPU cores, which on Render
# causes memory usage to exceed the 8 GB build limit.  Limiting to 1
# parallel job keeps peak RAM at ~1-2 GB.
ENV CMAKE_BUILD_PARALLEL_LEVEL=1
ENV MAKEFLAGS="-j1"

RUN pip install --no-cache-dir --upgrade pip

# Install dlib first, alone, so the heavy C++ compile stays within memory.
RUN pip install --no-cache-dir dlib

# Now install everything else (face_recognition will see dlib is already
# present and skip recompilation).
COPY requirements-render.txt .
RUN pip install --no-cache-dir -r requirements-render.txt

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
