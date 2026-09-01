import cv2
import numpy as np
import math
import os
import shutil
import argparse

# ── 인자 파싱 ─────────────────────────────────────────
parser = argparse.ArgumentParser(description="번호판 이미지 기하학적 변형 증강")
parser.add_argument("--src",  type=str, required=True,  help="입력 루트 폴더 (예: result33)")
parser.add_argument("--dst",  type=str, required=True,  help="출력 루트 폴더  (예: result6)")
parser.add_argument("--type", type=str, default="all",
                    choices=["all", "rotate", "shift"],
                    help="변형 종류: all=4종 / rotate=회전만 / shift=전단만")
parser.add_argument("--n",    type=int, default=0,
                    help="입력 이미지 중 무작위 샘플 수 (0=전체 사용)")
args = parser.parse_args()

# ── 경로 설정 ─────────────────────────────────────────
image_dir      = os.path.join(args.src, "images")
label_dir      = os.path.join(args.src, "labels")
save_image_dir = os.path.join(args.dst, "images")
save_label_dir = os.path.join(args.dst, "labels")

os.makedirs(save_image_dir, exist_ok=True)
os.makedirs(save_label_dir, exist_ok=True)

# ── 변형 종류 선택 ────────────────────────────────────
ALL_TRANSFORMS = {
    "l":  "left_rotate",
    "r":  "right_rotate",
    "lp": "left_shear",
    "rp": "right_shear",
}

if args.type == "rotate":
    transformations = {k: v for k, v in ALL_TRANSFORMS.items() if k in ("l", "r")}
elif args.type == "shift":
    transformations = {k: v for k, v in ALL_TRANSFORMS.items() if k in ("lp", "rp")}
else:
    transformations = ALL_TRANSFORMS

# ── 변형 함수 ─────────────────────────────────────────
def get_safe_rotation_size(w, h, angle_deg):
    angle_rad = math.radians(abs(angle_deg))
    new_w = int(h * math.sin(angle_rad) + w * math.cos(angle_rad))
    new_h = int(h * math.cos(angle_rad) + w * math.sin(angle_rad))
    return new_w, new_h


def transform_image(img, transform_type):
    h, w = img.shape[:2]

    if transform_type == "l":
        angle = 5
        new_w, new_h = get_safe_rotation_size(w, h, angle)
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        M[0, 2] += (new_w - w) / 2
        M[1, 2] += (new_h - h) / 2
        return cv2.warpAffine(img, M, (new_w, new_h), borderValue=(255, 255, 255))

    elif transform_type == "r":
        angle = -5
        new_w, new_h = get_safe_rotation_size(w, h, angle)
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        M[0, 2] += (new_w - w) / 2
        M[1, 2] += (new_h - h) / 2
        return cv2.warpAffine(img, M, (new_w, new_h), borderValue=(255, 255, 255))

    elif transform_type == "lp":
        # 수평 전단 — 아래쪽 행이 오른쪽으로 밀림 (좌측 기울기)
        # x' = x + shear * y  →  평행사변형 형태, 높이 유지
        shear = 0.15  # tan(~8.5°)
        new_w = int(w + shear * h)
        M = np.float32([[1, shear, 0], [0, 1, 0]])
        return cv2.warpAffine(img, M, (new_w, h), borderValue=(255, 255, 255))

    elif transform_type == "rp":
        # 수평 전단 — 아래쪽 행이 왼쪽으로 밀림 (우측 기울기)
        # x' = x - shear * y + offset
        shear = 0.15
        new_w = int(w + shear * h)
        M = np.float32([[1, -shear, shear * h], [0, 1, 0]])
        return cv2.warpAffine(img, M, (new_w, h), borderValue=(255, 255, 255))


# ── 파일 목록 수집 및 샘플링 ──────────────────────────
all_files = [f for f in os.listdir(image_dir) if f.lower().endswith('.jpg')]

if args.n > 0:
    import random
    random.seed(42)
    all_files = random.sample(all_files, min(args.n, len(all_files)))
    print(f"샘플링: {len(all_files)}장 선택")

# ── 메인 루프 ─────────────────────────────────────────
skipped = 0
saved   = 0

for file in all_files:
    filename   = os.path.splitext(file)[0]
    image_path = os.path.join(image_dir, file)
    label_path = os.path.join(label_dir, filename + ".txt")

    if not os.path.exists(label_path):
        print(f"[SKIP] 라벨 없음: {file}")
        skipped += 1
        continue

    img = cv2.imread(image_path)
    if img is None:
        print(f"[SKIP] 이미지 로딩 실패: {file}")
        skipped += 1
        continue

    for suffix in transformations:
        transformed_img = transform_image(img, suffix)

        save_img_path = os.path.join(save_image_dir, f"{filename}_{suffix}.jpg")
        save_lbl_path = os.path.join(save_label_dir, f"{filename}_{suffix}.txt")

        cv2.imwrite(save_img_path, transformed_img)
        shutil.copy2(label_path, save_lbl_path)
        saved += 1

# ── 결과 출력 ─────────────────────────────────────────
print(f"\n완료 — 저장: {saved}장 / 건너뜀: {skipped}장")
print(f"출력 경로: {args.dst}")
