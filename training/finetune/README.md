# Fine-tuning

- `train.py` — 파인튜닝 실행 스크립트 (PyTorch Lightning, `config/kor_config.yaml` 사용, `max_epochs=300`, `patience=30`)
- `export_onnx.py` — 학습된 체크포인트(.ckpt/.pt) → ONNX 변환 스크립트

실행 예시:

```bash
python train.py
python export_onnx.py --ckpt <checkpoint>.ckpt --output lprnet_kor.onnx
```

실제 실행 로그와 ONNX 변환·평가 과정은 [`../notebooks/lprnet_kor_finetune_onnx_eval.ipynb`](../notebooks/lprnet_kor_finetune_onnx_eval.ipynb) 참고.
