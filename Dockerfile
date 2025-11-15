FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

# 1. Run the posting script ONCE (it can auto-generate topics)
# 2. Stay alive on port 3000 so Coolify stays healthy
CMD ["bash", "-c", "python ai_script.py || true; python -m http.server 3000"]
