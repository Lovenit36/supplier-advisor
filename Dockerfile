FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir -U pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY static ./static
COPY data/pumps.json ./data/pumps.json
RUN mkdir -p /app/data
ENV PORT=8000 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
