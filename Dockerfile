FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080 BEHIND_PROXY=1
CMD gunicorn -w 2 -k gthread --threads 8 -t 90 -b 0.0.0.0:$PORT app:app
