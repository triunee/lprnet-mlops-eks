# LPRNet — 한국 번호판 인식 EKS 배포

Google Colab에서 파인튜닝한 LPRNet 모델을 FastAPI 추론 서버로 래핑하고 AWS EKS에 배포하는 MLOps 파이프라인입니다.

## 베이스 모델

[kwon-evan/LPRNet](https://github.com/kwon-evan/LPRNet) 을 기반으로 한국 번호판 데이터셋에 파인튜닝하였습니다.

- 원본 모델: PyTorch Lightning 기반 LPRNet (CTC Loss)
- 변환: ONNX (opset 18, dynamic batch)
- 추론: ONNX Runtime (FastAPI 서버)

## 아키텍처

```
GitHub push
    → GitHub Actions (docker build + ECR push + EKS 롤링 배포)
    → 배포 완료 후 자동 평가 (S3 test 이미지 → NLB /predict → CloudWatch)
    → Grafana 대시보드 (인프라 + 모델 정확도 통합 시각화)
```

```
[클라이언트]
     │
     ▼
[NLB (인터넷 facing)]
     │
     ▼
[EKS 클러스터 - lprnet-cluster]
  ├─ lprnet-inference Pod x2~5 (t3.medium Spot)
  │    ├─ FastAPI (port 8080)
  │    ├─ ONNX Runtime
  │    └─ /metrics (Prometheus)
  └─ monitoring namespace
       ├─ Prometheus
       └─ Grafana

[평가 자동화]
  S3 (test 이미지) → GitHub Actions → NLB /predict → CloudWatch → Grafana
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| 모델 | LPRNet (PyTorch → ONNX, opset 18) |
| 추론 서버 | FastAPI + uvicorn + ONNX Runtime |
| 인프라 | AWS EKS (Kubernetes 1.35), Terraform |
| 이미지 저장소 | AWS ECR |
| CI/CD | GitHub Actions (OIDC 인증) |
| 모니터링 | Prometheus + Grafana (kube-prometheus-stack) |
| 메트릭 | AWS CloudWatch (LPRNet/ModelEval) |
| 스케일링 | HPA (CPU 70% 초과 시 Pod 2 → 5) |

## 데이터셋

> 번호판 이미지 생성 코드는 별도 레포지토리에 공개 예정입니다.

### 번호판 종류별 구성

| 폴더 | 생성 스크립트 | 설명 |
|------|-------------|------|
| `result2/` | `gen_car.py` | 일반 승용차 번호판. 가로형(Type A, 21종 템플릿) + 세로형(Type B, 6종). 지역명 없는 새 형식 (예: `12가3456`) |
| `result3/` | `gen_truck.py` | 화물·영업용 번호판. 1줄형(Type D, 3종) + 2줄형(Type C, 11종). 지역명 포함 (예: `경기80사2983`) |
| `result32/` | `gen_truck_8digit.py` | 화물차 8자리 전용. 가로형(Type A). 번호 범위 800~979 (예: `800배4482`) |
| `result33/` | `gen_car_military.py` | 일반 승용차 + 군용 번호판. 군용 한글(공/국/해/합/육) 포함 (예: `11공2625`) |
| `result6/` | `augment.py` | result33 이미지에 기하학적 변형(회전·원근 등) 증강 적용. 접미사 `_l`, `_r`, `_lp`, `_rp` |

### 데이터셋 분할 (stratified split, 70/15/15)

| 폴더 | train | val | test | 합계 |
|------|------:|----:|-----:|-----:|
| result2/ | 3,042 | 652 | 652 | 4,346 |
| result3/ | 1,342 | 287 | 287 | 1,916 |
| result32/ | 1,029 | 220 | 220 | 1,469 |
| result33/ | 132 | 28 | 28 | 188 |
| result6/ | 1,391 | 298 | 298 | 1,987 |
| **합계** | **6,757** | **1,447** | **1,452** | **9,656** |

### S3 구조

```
s3://lprnet-bucket/
├── dataset/
│   ├── train/          # 학습용 (6,757장)
│   ├── val/            # 검증용 (1,447장)
│   └── test/           # 평가 자동화 전용 (1,452장)
├── eval-results/       # 평가 결과 JSON 이력
└── models/             # ONNX 모델 가중치
    ├── lprnet_kor_v1.onnx
    └── lprnet_kor_v1.onnx.data
```

## 실험 결과

| 항목 | 결과 |
|------|------|
| 모델 정확도 — test 셋 (1,452장) | **94.28%** (1,369 / 1,452) |
| 모델 정확도 — val 셋 (1,449장) | 94.82% (1,374 / 1,449) |
| 추론 지연시간 (Pod 내부) | **~74ms** |
| 추론 지연시간 (클라이언트 기준) | ~89ms |
| HPA 스케일아웃 | 정상 (CPU 70% 초과 → Pod 2 → 3) |
| CloudWatch 전송 | 정상 (LPRNet/ModelEval 네임스페이스) |

> test 셋은 학습·검증에 사용되지 않은 독립 데이터. val과 차이 0.54%p → 과적합 없음 확인

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

## 평가 자동화 파이프라인

```
EKS 배포 완료 (deploy.yml)
        │
        ▼ 자동 트리거
[eval.yml — GitHub Actions]
        │
        ├─ OIDC 기반 AWS 인증
        ├─ S3에서 test 이미지 다운로드 (1,452장)
        ├─ NLB /predict 순차 호출
        ├─ 정확도 계산 (NFC 정규화 포함)
        ├─ CloudWatch Metrics 전송
        │    Namespace: LPRNet/ModelEval
        │    Metrics: Accuracy, CorrectCount, TotalCount
        ├─ S3 JSON 이력 저장
        └─ GitHub Actions Summary 출력
```

## GitHub Actions Variables / Secrets

| 종류 | 이름 | 설명 |
|------|------|------|
| Variable | `S3_BUCKET` | S3 버킷명 |
| Variable | `MODEL_VERSION` | 모델 버전 (예: v1.0) |
| Secret | `AWS_ACCOUNT_ID` | AWS 계정 ID |
| Secret | `NLB_URL` | NLB 엔드포인트 |

## 배포 절차

```bash
# 1. S3에 모델 및 test 데이터 업로드
aws s3 cp lprnet_kor_finetuned4.onnx s3://<S3_BUCKET>/models/lprnet_kor_v1.onnx
aws s3 cp lprnet_kor_finetuned4.onnx.data s3://<S3_BUCKET>/models/lprnet_kor_v1.onnx.data
aws s3 sync ./dataset/test/ s3://<S3_BUCKET>/dataset/test/

# 2. Terraform 인프라 구성 (2단계 적용 필요)
cd terraform
terraform apply -target=module.eks   # 1단계: EKS 클러스터
terraform apply                      # 2단계: LBC 등 나머지

# 3. EKS 배포
aws eks update-kubeconfig --region ap-northeast-2 --name lprnet-cluster
envsubst < k8s/deployment.yaml | kubectl apply -f -
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# 4. Prometheus + Grafana 설치
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -f k8s/monitoring/prometheus-values.yaml \
  -n monitoring --create-namespace
kubectl apply -f k8s/monitoring/servicemonitor.yaml

# 5. GitHub Actions 설정 후 push → 자동 배포 + 평가 트리거
```

## 트러블슈팅

### NAT Gateway 미생성으로 노드 조인 실패
- **증상:** `NodeCreationFailure` (30분 대기)
- **원인:** `-target=module.eks` 시 NAT Gateway가 생성되지 않아 Private 노드가 EKS에 조인 불가
- **해결:**
```bash
terraform apply -target=aws_nat_gateway.main -target=aws_route.private_nat
terraform apply
```

### Docker 이미지 아키텍처 불일치
- **증상:** `no match for platform in manifest`
- **원인:** Apple Silicon(arm64) 빌드 → EKS t3.medium(amd64) 실행 불가
- **해결:** `--platform linux/amd64` 명시

### 한글 인코딩 비교 오류
- **증상:** 정답과 추론이 같아 보여도 비교 결과 X
- **원인:** macOS 파일명(NFD) vs API 응답(NFC) 차이
- **해결:** `unicodedata.normalize('NFC', ...)` 양쪽 통일

## 비용 참고 (ap-northeast-2)

| 리소스 | 시간당 |
|--------|--------|
| EKS 컨트롤 플레인 | $0.10 |
| NAT Gateway | $0.045 |
| NLB | $0.0225 |
| t3.medium Spot x2 | ~$0.021 |
| **합계** | **~$0.19/h ($4.5/일)** |

> 사용 후 `terraform destroy`로 리소스 삭제 필요

## References

- [kwon-evan/LPRNet](https://github.com/kwon-evan/LPRNet) — 베이스 모델
- [LPRNet: License Plate Recognition via Deep Neural Networks](https://arxiv.org/abs/1806.10447v1)
