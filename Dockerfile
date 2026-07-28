FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (WeasyPrint needs these on Linux)
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-dev \
    libffi-dev \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader stopwords wordnet

COPY . .

EXPOSE 5000

# Ensure directories exist
RUN mkdir -p /app/instance /app/models_saved /app/uploads /app/reports /app/data

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
