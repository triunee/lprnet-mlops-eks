# ALPR 한국 번호판 데이터셋 생성

## 프로젝트 개요
한국 번호판 합성 이미지 생성 및 kwon-evan/LPRNet 학습용 포맷 변환 파이프라인.
타겟 모델: kwon-evan/LPRNet (입력 규격: **100×50px**, RGB, 파일명 = 라벨)

---

## 디렉토리 구조

```
ALPRData/
├── assets/
│   ├── plates/type_a/     # 일반 가로형 21종
│   ├── plates/type_b/     # 일반 세로형 6종
│   ├── plates/type_c/     # 화물 2줄형 11종
│   ├── plates/type_d/     # 화물 1줄형 3종
│   ├── chars/             # 일반 한글 40종 (가~주, 단 기-row·히·카·파·타·차·영 미포함)
│   ├── chars_truck/       # 화물 한글 5종 (아/바/배/자/사)
│   ├── chars_m/           # 군용 한글 5종 (공/국/해/합/육)
│   ├── nums/              # 숫자 0~9
│   ├── region1/           # 지역명 앞글자 17종
│   └── region2/           # 지역명 뒷글자 17종
│
├── gen_car.py             # 일반 승용차 번호판      → result2/
├── gen_car_military.py    # 일반 + 군용 번호판      → result33/
├── gen_truck_8digit.py    # 화물차 8자리 전용       → result32/
├── gen_truck.py           # 화물/영업용 번호판      → result3/
├── augment.py             # 기하학적 변형 증강      → result6/
├── prepare_lprnet.py      # LPRNet 전용 변환 (신규) → dataset/
│
├── result2/               # 생성 이미지 (파일명 = 번호판 텍스트)
├── result3/
├── result6/
├── result32/
├── result33/
│
├── output/                # TAO Toolkit 전용 — LPRNet에 사용 불가
├── dataset/train/         # LPRNet 학습용 최종 출력 (100×50px 플랫 구조)
└── dataset/val/
```

---

## 실행 순서

```bash
# 1. 이미지 생성 (병렬 실행 가능)
python gen_car.py
python gen_car_military.py
python gen_truck_8digit.py
python gen_truck.py

# 2. 변형 증강 (gen_car_military 완료 후)
python augment.py

# 3. LPRNet 전용 변환 (모든 생성 완료 후)
python prepare_lprnet.py
```

---

## num_img 설정값

| 파일 | 현재값 | 권장값 | 현재 생성량 |
|---|---|---|---|
| `gen_car.py` | `161` | `190` 이상 | 4,347장 |
| `gen_car_military.py` | `7` | `50` 이상 | 189장 |
| `gen_truck_8digit.py` | `70` | 유지 | 1,470장 |
| `gen_truck.py` | `137` | 유지 | 1,918장 |

---

## LPRNet 입력 호환 여부

### 폴더별 포함 타입

| 결과 폴더 | 포함 타입 | 장수 | 1줄/2줄 |
|---|---|---|---|
| result2/ | Type A (가로 1줄, 21종) | 3,381장 | 1줄 |
| result2/ | Type B (세로형 1줄, 6종) | 966장 | 1줄 |
| result33/ | Type A (가로 1줄, 21종) | 147장 | 1줄 |
| result33/ | Type B (세로형 1줄, 6종) | 42장 | 1줄 |
| result32/ | Type A (가로 1줄, 21종, plate_21 포함) | 1,470장 | 1줄 |
| result3/ | Type D (화물 1줄, 3종) | 411장 | 1줄 |
| result3/ | Type C (화물 2줄, 11종) | 1,507장 | **2줄** |
| result6/ | result33/ 증강 (type_a + type_b) | 1,988장 | 1줄 |

### prepare_lprnet.py 처리 방식

| 타입 | 처리 방식 | 지원 여부 |
|---|---|---|
| Type A / Type B / Type D — 1줄 | 100×50 리사이즈 | ✅ 즉시 사용 가능 |
| Type C — 화물 2줄 (result3/) | 2줄 병합 후 100×50 리사이즈 | ⚠️ 미구현 |

> **Type B**는 템플릿 모양만 다를 뿐 모든 문자가 단일 행(y=45)에 배치 → 1줄로 분류
> **Type C**만 진짜 2행 레이아웃 (상단: 지역명+번호2자, 하단: 한글+번호4자)
>
> **1줄 바로 사용 가능**: 3,381 + 966 + 147 + 42 + 1,470 + 411 + 1,988 = **8,405장**
> **2줄 처리 필요**: Type C만 — **1,507장**

> 지역명(`서울`, `경기` 등)은 모델 chars에서 2글자 단일 토큰으로 정의됨 — LPRNet data loader가 longest-match로 처리하므로 파일명 그대로 라벨로 사용 가능.

---

## output/ vs dataset/ 포맷 차이

`output/`(TAO용)은 `images/` + `labels/` 분리 구조에 순번 파일명(`00001.jpg`)이므로
LPRNet에 사용 불가. `prepare_lprnet.py`로 `dataset/`에 별도 변환 필요.

---

## 현재 데이터셋 문자 커버리지

모델(kwon-evan/LPRNet) chars 기준으로 우리 데이터셋에 **없는 문자 14종**:

| 분류 | 모델 지원 | 데이터셋 누락 |
|---|---|---|
| 자가용 기-row | 기/니/디/리/미/비/시/이/지 | **9자 전체** |
| 렌터카 | 하/허/호/히 | **히** |
| 영업용 | 바/사/아/자/카/파/타/차 | **카/파/타/차** |
| 영업용(건설) | 영 | **영** |

→ 파인튜닝 후 이 14자가 포함된 실제 번호판에서 인식률 저하 가능성.
→ 대응: `assets/chars/`에 해당 글자 이미지 추가 후 스크립트 재생성.

---

## 규칙 및 주의사항

- `assets/` 파일명 변경 금지 — 스크립트가 `sorted()` 순서에 의존
- `character_list.txt` 수정 시 `assets/chars*/` 폴더와 반드시 동기화
- 파일명 = 라벨 — `prepare_lprnet.py`가 파일명을 그대로 라벨로 사용
- 중복 번호판 파일명에 `_1`, `_2` 접미사가 붙음 — prepare_lprnet.py에서 `re.sub(r'_\d+$', '', stem)` 으로 접미사 제거 후 라벨 추출 필요
- `augment.py` 평행이동(80px) 변형은 YOLO 라벨 미갱신 버그 있음
  (prepare_lprnet.py는 YOLO 라벨 미사용이므로 무관하나 이미지 품질에 영향)
- `num_img < 문자셋 크기`이면 일부 문자만 생성됨 — num_img 설정 시 확인 필요
- `nums/` 로딩 시 반드시 `sorted(os.listdir())` 사용 — 미정렬 시 인덱스-digit 불일치 버그 발생 (gen_car.py, gen_car_military.py에 적용 완료)

---

## prepare_lprnet.py 구현 요구사항

| 항목 | 내용 |
|---|---|
| 리사이즈 | `cv2.resize(img, (100, 50))` — W×H |
| 라벨 추출 | `re.sub(r'_\d+$', '', Path(f).stem)` |
| plate_21 필터 | result32/ 소스에서 파일명에 `plate_21` 포함 시 제외 |
| 소스 폴더 | result2, result3, result32, result33, result6 |
| plate_21 처리 | 포함 — 스크립트에서 이미 위치/크기 조정 완료 (별도 필터링 불필요) |
| 출력 구조 | flat (`dataset/train/`, `dataset/val/`) |
| train/val 분할 | 85% / 15% (random seed 고정) |
| 학습 경로 설정 | idn_config.yaml의 `train_dir` / `valid_dir`를 `dataset/` 기준으로 수정 |

---

## TODO

- [x] `gen_car.py` num_img=161 설정 완료
- [x] `nums/` sorted() 버그 수정 (gen_car.py, gen_car_military.py)
- [x] 번호 범위 수정 (승용차 10~79 / 100~799, 화물 80~97 / 800~979)
- [ ] `prepare_lprnet.py` 신규 작성
- [ ] `idn_config.yaml` train_dir / valid_dir 경로 수정
- [ ] 누락 14자 assets 추가 (기/니/디/리/미/비/시/이/지/히/카/파/타/차/영)
- [x] plate_21 반사판 처리 완료 — 스크립트 내 위치/크기 조정으로 포함 (필터링 불필요)
- [ ] Type B / Type C 2줄 병합 파일명 규칙 확정 및 생성 스크립트 반영
- [ ] 화물 번호판 비중 조정 — num_img 재설정으로 균형 맞추기
