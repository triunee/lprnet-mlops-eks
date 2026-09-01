import os
import re
import random
import yaml
import cv2
from pathlib import Path
from tqdm import tqdm

SRC_DIRS    = ["result2", "result3", "result32", "result33", "result6"]
TRAIN_DIR   = "./dataset2/train"
VAL_DIR     = "./dataset2/val"
TEST_DIR    = "./dataset2/test"
TRAIN_RATIO = 0.70
VAL_RATIO   = 0.15
# 나머지 0.15가 test
RANDOM_SEED = 42
IMG_SIZE    = (100, 50)  # (width, height) for cv2.resize

print("[1/5] kor_config.yaml 로드 중...")
with open("./kor_config.yaml", encoding="utf-8") as f:
    cfg = yaml.full_load(f)
CHARS = cfg["chars"]
print(f"      chars 로드 완료: {len(CHARS)}개 토큰\n")


def is_valid_label(label: str) -> bool:
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


def extract_label(filepath) -> str:
    stem = Path(filepath).stem
    stem = re.sub(r'_(lp|rp|l|r)$', '', stem)  # 증강 접미사 제거 (_l, _r, _lp, _rp)
    stem = re.sub(r'_\d+$', '', stem)           # 중복 접미사 제거 (_1, _2 등)
    return stem


def process_image(src_path: str, dst_path: str) -> bool:
    img = cv2.imread(src_path)
    if img is None:
        return False
    img = cv2.resize(img, IMG_SIZE, interpolation=cv2.INTER_CUBIC)
    cv2.imwrite(dst_path, img)
    return True


def save_split(file_list, dst_dir, desc):
    counter = {}
    for src_path, label in tqdm(file_list, desc=desc):
        counter[label] = counter.get(label, 0) + 1
        dst_name = f"{label}_{counter[label]}.jpg"
        dst_path = os.path.join(dst_dir, dst_name)
        if not process_image(str(src_path), dst_path):
            print(f"[ERROR] 읽기 실패: {src_path}")


random.seed(RANDOM_SEED)

print("[2/5] 소스 폴더에서 이미지 수집 중...")
all_files = []
for src in SRC_DIRS:
    before = len(all_files)
    for ext in ("*.jpg", "*.png", "*.jpeg"):
        all_files.extend(Path(src, "images").glob(ext))
    print(f"      {src}/: {len(all_files) - before}장")
print(f"      합계: {len(all_files)}장\n")

print("[3/5] 라벨 유효성 검사 중...")
# 폴더별로 분리하여 수집 (계층 분할을 위해)
per_src = {src: [] for src in SRC_DIRS}
skip_count = 0
for f in all_files:
    src_key = f.parts[0]  # 'result2', 'result33' 등
    label = extract_label(f)
    if is_valid_label(label):
        per_src[src_key].append((f, label))
    else:
        print(f"[SKIP] {f.name}  ←  미등록 문자 포함: '{label}'")
        skip_count += 1

total_valid = sum(len(v) for v in per_src.values())
print(f"      유효: {total_valid}장 / 스킵: {skip_count}장\n")

print("[4/5] 폴더별 계층 분할(stratified) train/val/test 중...")
train_files, val_files, test_files = [], [], []
for src, files in per_src.items():
    random.shuffle(files)
    t_end = int(len(files) * TRAIN_RATIO)
    v_end = int(len(files) * (TRAIN_RATIO + VAL_RATIO))
    train_files += files[:t_end]
    val_files   += files[t_end:v_end]
    test_files  += files[v_end:]
    print(f"      {src}/: train {len(files[:t_end])} / val {len(files[t_end:v_end])} / test {len(files[v_end:])}")

# 폴더 순서 편향 제거를 위해 각 split 내부도 셔플
random.shuffle(train_files)
random.shuffle(val_files)
random.shuffle(test_files)
print(f"      합계  : train {len(train_files)} / val {len(val_files)} / test {len(test_files)}\n")

print("[5/5] 이미지 저장 중...")
os.makedirs(TRAIN_DIR, exist_ok=True)
os.makedirs(VAL_DIR,   exist_ok=True)
os.makedirs(TEST_DIR,  exist_ok=True)

save_split(train_files, TRAIN_DIR, "train")
save_split(val_files,   VAL_DIR,   "val  ")
save_split(test_files,  TEST_DIR,  "test ")

print(f"\n완료!")
print(f"  train : {len(train_files)}장  →  {TRAIN_DIR}")
print(f"  val   : {len(val_files)}장  →  {VAL_DIR}")
print(f"  test  : {len(test_files)}장  →  {TEST_DIR}")
