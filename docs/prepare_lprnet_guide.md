# prepare_lprnet.py 작성 가이드라인

## 개요

`ALPRData/` 내 result 폴더의 합성 번호판 이미지를 읽어
kwon-evan/LPRNet 학습 포맷(`dataset/train/`, `dataset/val/`)으로 변환하는 스크립트.

- 입력: `result2/`, `result3/`, `result32/`, `result33/`, `result6/`
- 출력: `dataset/train/`, `dataset/val/` (100×50px, 파일명 = 라벨)
- 참조 모델 코드: `lprnet/datamodule.py`, `lprnet/utils.py`, `config/kor_config.yaml`

---

## 파일 위치 및 실행 기준

```
ALPRData/
├── prepare_lprnet.py   ← 여기에 작성
├── result2/
├── result3/
├── result32/
├── result33/
├── result6/
└── dataset/
    ├── train/          ← 출력
    └── val/            ← 출력
```

실행:

```bash
cd ALPRData/
python prepare_lprnet.py
```

---

## 상수 정의

```python
import os, re, random, yaml, cv2
from pathlib import Path
from tqdm import tqdm

SRC_DIRS    = ["result2", "result3", "result32", "result33", "result6"]
TRAIN_DIR   = "dataset/train"
VAL_DIR     = "dataset/val"
TRAIN_RATIO = 0.85
RANDOM_SEED = 42
IMG_SIZE    = (100, 50)   # (W, H) — cv2.resize 는 width 먼저
```

---

## 1단계 — chars 로드 및 유효성 검사 함수

### 왜 필요한가

`lprnet/utils.py encode()` 함수는 chars 목록에 없는 문자를 만나면
`assert 0, "no such char"` 로 학습 전체를 중단시킵니다.
사전에 걸러야 합니다.

### chars 로드

```python
with open("../config/kor_config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
CHARS = cfg["chars"]   # list[str], 단일 문자 + 지역명 2글자 포함
```

### longest-match 유효성 검사

`lprnet/utils.py:6` `encode()` 와 동일한 로직으로 구현합니다.

```python
def is_valid_label(label: str) -> bool:
    """chars 목록으로 label 전체를 longest-match 분해 가능한지 확인."""
    i = 0
    while i < len(label):
        j = len(label)
        matched = False
        while i < j:
            if label[i:j] in CHARS:
                i = j
                matched = True
                break
            j -= 1
        if not matched:
            return False
    return True
```

---

## 2단계 — 라벨 추출 함수

### 규칙 (dataset.md 및 datamodule.py:91 기준)

| 처리 | 이유 |
|---|---|
| `re.sub(r'_\d+$', '', stem)` | `_1`, `_2` 중복 접미사 제거 |
| `-` 분리 불필요 | 한국 번호판에 `-` 없음 (IDN 전용) |
| `.upper()` 불필요 | 한글은 대소문자 무관 |

```python
def extract_label(filepath) -> str:
    stem = Path(filepath).stem              # 확장자 제거
    stem = re.sub(r'_\d+$', '', stem)       # 중복 접미사 제거
    return stem
```

> **주의**: `datamodule.py`는 `split("_")[0]`으로 라벨을 추출합니다.
> 출력 파일명에 `_숫자` 이외의 언더스코어가 포함되면 라벨이 잘립니다.
> 출력 파일명 형식은 반드시 `{라벨}_{카운터}.jpg` 를 사용하세요.

---

## 3단계 — 이미지 처리 함수

```python
def process_image(src_path: str, dst_path: str) -> bool:
    img = cv2.imread(src_path)
    if img is None:
        return False
    img = cv2.resize(img, IMG_SIZE, interpolation=cv2.INTER_CUBIC)
    cv2.imwrite(dst_path, img)
    return True
```

- `IMG_SIZE = (100, 50)` — cv2.resize 인자는 `(width, height)` 순서
- `INTER_CUBIC` — `datamodule.py:86` 과 동일한 보간 방식

---

## 4단계 — 전체 흐름

```python
random.seed(RANDOM_SEED)

# --- 수집 ---
all_files = []
for src in SRC_DIRS:
    for ext in ("*.jpg", "*.png", "*.jpeg"):
        all_files.extend(Path(src).glob(ext))

# --- 필터링 ---
valid_files = []
skip_log = []
for f in all_files:
    label = extract_label(f)
    if is_valid_label(label):
        valid_files.append((f, label))
    else:
        skip_log.append((str(f), label))

for path, label in skip_log:
    print(f"[SKIP] {Path(path).name}  ←  미등록 문자 포함: '{label}'")
print(f"\n유효: {len(valid_files)}장 / 스킵: {len(skip_log)}장")

# --- 셔플 및 분할 ---
random.shuffle(valid_files)
split       = int(len(valid_files) * TRAIN_RATIO)
train_files = valid_files[:split]
val_files   = valid_files[split:]

# --- 출력 폴더 생성 ---
os.makedirs(TRAIN_DIR, exist_ok=True)
os.makedirs(VAL_DIR,   exist_ok=True)

# --- 저장 ---
def save_split(file_list, dst_dir, desc):
    counter = {}
    for src_path, label in tqdm(file_list, desc=desc):
        counter[label] = counter.get(label, 0) + 1
        dst_name = f"{label}_{counter[label]}.jpg"
        dst_path = os.path.join(dst_dir, dst_name)
        if not process_image(str(src_path), dst_path):
            print(f"[ERROR] 읽기 실패: {src_path}")

save_split(train_files, TRAIN_DIR, "train")
save_split(val_files,   VAL_DIR,   "val  ")

print(f"\ntrain : {len(train_files)}장  →  {TRAIN_DIR}")
print(f"val   : {len(val_files)}장  →  {VAL_DIR}")
```

---

## 5단계 — kor_config.yaml 경로 수정

`prepare_lprnet.py` 실행 완료 후, LPRNet 프로젝트의
`config/kor_config.yaml` 경로를 아래와 같이 수정합니다.

```yaml
# LPRNet-master/ 기준 상대경로
train_dir: 'ALPRData/dataset/train/'
valid_dir: 'ALPRData/dataset/val/'
pretrained: 'weights/lprnet_kor.pt'
```

---

## 주의사항 체크리스트

| 항목 | 세부 내용 |
|---|---|
| `IMG_SIZE = (100, 50)` | cv2는 `(width, height)` — 반대로 쓰면 50×100 됨 |
| 출력 파일명 형식 | `{라벨}_{카운터}.jpg` 고정 — `-` 또는 `_문자` 삽입 금지 |
| chars 기준 파일 | `kor_config.yaml` 사용 — `idn_config.yaml` 아님 |
| 지역명 2글자 토큰 | `서울`, `경기` 등은 chars에 단일 토큰으로 등록됨 — longest-match로 올바르게 분해됨 |
| result32 plate_21 | 별도 필터링 불필요 — 스크립트 내에서 이미 처리 완료 |
| Type B / Type C (2줄) | 현재 1줄 번호판만 지원 — 2줄 병합 미구현 상태로 스킵됨 |
| random.seed 고정 | 재현 가능한 train/val 분할 보장 |

---

## 실제 출력 통계

### 소스 폴더별 수집량

| 폴더 | 장수 | 비고 |
|---|---|---|
| result2/ | 4,347장 | Type A + Type B |
| result3/ | 1,918장 | Type D (411) + Type C 2줄 (1,507) |
| result32/ | 1,470장 | Type A (화물 8자리) |
| result33/ | 189장 | Type A + Type B (군용) |
| result6/ | 1,988장 | result33 증강 (type_a + type_b) |
| **합계** | **9,912장** | |

### 필터링 및 분할 결과

| 항목 | 장수 |
|---|---|
| 전체 수집 | 9,912장 |
| 스킵 (세종·울산 지역명) | 256장 |
| 유효 | 9,656장 |
| train (85%) | 8,207장 |
| val (15%) | 1,449장 |

> **세종·울산 스킵 이유**: `kor_config.yaml` chars 목록에 미등록. 프리트레인 가중치 호환 유지를 위해 추가하지 않음.
> Type C 2줄 번호판(1,507장)은 현재 미구현으로 스킵됨 — 구현 시 추가 확보 가능.

---

## 관련 파일 참조

| 파일 | 참조 목적 |
|---|---|
| `lprnet/utils.py:6` `encode()` | 라벨 유효성 검사 로직 동일하게 구현 |
| `lprnet/datamodule.py:89-92` | 파일명에서 라벨 추출 방식 확인 |
| `config/kor_config.yaml` | chars 목록 로드 |
| `dataset.md` | 소스 폴더 구성 및 요구사항 전체 명세 |
