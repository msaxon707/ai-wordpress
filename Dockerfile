FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

# Keep the container alive for Coolify health checks.
# DO NOT run the autoposter automatically.
CMD ["python", "-m", "http.server", "3000"]
