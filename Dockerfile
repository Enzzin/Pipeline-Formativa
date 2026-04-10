FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

CMD ["sh", "-c", "python -c 'from main import init_db; init_db()' && uvicorn main:app --host 0.0.0.0 --port 8000"]