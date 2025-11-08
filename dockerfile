# Use a minimal Python image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Copy all files from your repo to the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the Python script when the container starts
CMD ["python", "ai_script.py"]

