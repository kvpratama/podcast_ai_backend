# Build the Docker image
docker build -t podcast-ai-backend .

# Run the container
docker run -d -p 8000:8000 podcast-ai-backend
