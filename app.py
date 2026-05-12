#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import warnings
import yaml
import cv2
import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

warnings.filterwarnings("ignore")

# ── 경로 설정 (Docker 컨테이너 기준 /app) ────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG    = os.path.join(BASE_DIR, "config", "kor_config.yaml")
ONNX_PATH = os.path.join(BASE_DIR, "lprnet_kor_finetuned4.onnx")

# ── 전역 초기화 ──────────────────────────────────────────────
with open(CONFIG, encoding="utf-8") as f:
    cfg = yaml.full_load(f)

CHARS = cfg["chars"]

if not os.path.exists(ONNX_PATH):
    raise FileNotFoundError(f"ONNX 파일 없음: {ONNX_PATH}")

if not os.path.exists(ONNX_PATH + ".data"):
    raise FileNotFoundError(f"ONNX data 파일 없음: {ONNX_PATH}.data")

sess = ort.InferenceSession(
    ONNX_PATH,
    providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
)

app = FastAPI(title="LPRNet 번호판 인식 API")
Instrumentator().instrument(app).expose(app)


# ── 전처리 ───────────────────────────────────────────────────
def preprocess(img_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지 디코딩 실패 — 유효한 이미지 파일인지 확인하세요")
    img = cv2.resize(img, (100, 50), interpolation=cv2.INTER_CUBIC)
    img = img.astype("float32")
    img -= 127.5
    img *= 0.0078125
    img = np.transpose(img, (2, 0, 1))
    return img[np.newaxis, ...]  # (1, 3, 50, 100)


# ── CTC 디코딩 ───────────────────────────────────────────────
def decode_ctc(output: np.ndarray) -> str:
    pred  = output[0]           # (110, 19)
    blank = len(CHARS) - 1
    result, pre = [], ""
    for j in range(pred.shape[1]):
        c = int(np.argmax(pred[:, j]))
        if c != pre and c != blank:
            result.append(CHARS[c])
        pre = c
    return "".join(result)


# ── 엔드포인트 ───────────────────────────────────────────────
@app.get("/health")
def health():
    """EKS liveness / readiness probe 용"""
    return {
        "status"     : "ok",
        "provider"   : sess.get_providers()[0],
        "chars_count": len(CHARS),
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    번호판 이미지를 업로드하면 인식 결과를 반환합니다.

    - **file**: jpg / png 이미지
    - **returns**: {"plate": "서울12가3456"}
    """
    if file.content_type not in (
        "image/jpeg", "image/png", "application/octet-stream"
    ):
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 형식: {file.content_type} (jpeg/png만 가능)",
        )

    try:
        img_bytes = await file.read()
        inp       = preprocess(img_bytes)
        output    = sess.run(["output"], {"input": inp})
        plate     = decode_ctc(output[0])
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추론 오류: {str(e)}")

    return JSONResponse({"plate": plate})