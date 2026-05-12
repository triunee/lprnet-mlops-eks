# LPRNet — 한국 번호판 인식 EKS 배포

Google Colab에서 파인튜닝한 LPRNet 모델을 FastAPI 추론 서버로 래핑하고 AWS EKS에 배포하는 MLOps 파이프라인입니다.

## 아키텍처

```
GitHub push
    → GitHub Actions (docker build + ECR push + EKS 롤링 배포)
    → 배포 완료 후 자동 평가 (S3 test 이미지 → NLB /predict → CloudWatch)
    → Grafana 대시보드 (인프라 + 모델 정확도 통합 시각화)
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| 모델 | LPRNet (PyTorch → ONNX) |
| 추론 서버 | FastAPI + ONNX Runtime |
| 인프라 | AWS EKS, ECR, S3, NLB (Terraform) |
| CI/CD | GitHub Actions (OIDC 인증) |
| 모니터링 | Prometheus + Grafana, CloudWatch |
| 스케일링 | HPA (CPU 70% 초과 시 Pod 2 → 5) |

## 실험 결과

| 항목 | 결과 |
|------|------|
| 모델 정확도 (test 1,452장) | **94.28%** |
| 추론 지연시간 | ~89ms |
| HPA 스케일아웃 | 정상 (CPU 70% 초과 → Pod 3) |

## API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/health` | GET | 헬스체크 |
| `/predict` | POST | 번호판 인식 (multipart/form-data) |
| `/metrics` | GET | Prometheus 메트릭 |

```bash
curl -X POST http://<NLB_URL>/predict -F "file=@plate.jpg"
# {"plate": "12가3456"}
```

## GitHub Actions Variables / Secrets

| 종류 | 이름 | 설명 |
|------|------|------|
| Variable | `S3_BUCKET` | S3 버킷명 |
| Variable | `MODEL_VERSION` | 모델 버전 (예: v1.0) |
| Secret | `AWS_ACCOUNT_ID` | AWS 계정 ID |
| Secret | `NLB_URL` | NLB 엔드포인트 |
| Secret | `GRAFANA_PASSWORD` | Grafana 접속 비밀번호 |

## References

- [LPRNet: License Plate Recognition via Deep Neural Networks](https://arxiv.org/abs/1806.10447v1)
- [sirius-ai/LPRNet_Pytorch](https://github.com/sirius-ai/LPRNet_Pytorch)
