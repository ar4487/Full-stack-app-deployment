FROM python:3.10-slim

WORKDIR /Backend

# Copy requirements.txt first
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Then copy the rest of the app
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


