# This Dockerfile is configured for Hugging Face Spaces (Free Tier, 16GB RAM)
# It builds and runs the FastAPI backend.

FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY backend/ .

# Hugging Face Spaces expects the app to run on port 7860
EXPOSE 7860

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
