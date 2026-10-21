FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=8080
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# The app creates data/mateis.db on first start. Mount /app/data as a volume to keep your edits.
EXPOSE 8080
CMD ["python", "main.py"]
