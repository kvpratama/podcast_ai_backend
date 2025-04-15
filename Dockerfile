# Use an official Python runtime as base
FROM python:3.12

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
# COPY ./app ./app

# Expose port
EXPOSE 8000

# Set environment variables (for production, use secrets manager or .env)
# ENV OPENAI_API_KEY="your-openai-api-key"

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
