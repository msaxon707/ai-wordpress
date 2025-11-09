# Use Python 3.11 slim image as the base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the main AI autoposter script
CMD ["python", "ai_script.py"]
