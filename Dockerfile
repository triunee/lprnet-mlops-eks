FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY lprnet_kor_finetuned4.onnx .
COPY lprnet_kor_finetuned4.onnx.data .
COPY config/kor_config.yaml config/kor_config.yaml
COPY app.py .

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
