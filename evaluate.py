# python3 evaluate.py --endpoint http://$NLB_URL --img_dir ./test_imgs --model_version v1.0

import argparse
import json
import os
import unicodedata
from datetime import datetime
from pathlib import Path

import boto3
import requests

BUCKET = os.environ["S3_BUCKET"]
NAMESPACE = "LPRNet/ModelEval"
REGION = os.environ.get("AWS_REGION", "ap-northeast-2")


def run_evaluation(endpoint: str, img_dir: str, model_version: str):
    img_dir = Path(img_dir)
    images = sorted(img_dir.glob("*.jpg"))
    total = len(images)
    correct = 0

    for idx, img_path in enumerate(images, start=1):
        ground_truth = unicodedata.normalize("NFC", img_path.stem)
        with open(img_path, "rb") as f:
            resp = requests.post(
                f"{endpoint}/predict",
                files={"file": (img_path.name, f, "image/jpeg")},
                timeout=10,
            )
        predicted = unicodedata.normalize("NFC", resp.json().get("plate", ""))
        is_correct = ground_truth == predicted
        if is_correct:
            correct += 1

        status = "O" if is_correct else "X"
        print(f"[{idx:4d}/{total}] 정답: {ground_truth} | 추론: {predicted} | {status}")

    accuracy = correct / total if total > 0 else 0.0

    cw = boto3.client("cloudwatch", region_name=REGION)
    dimensions = [{"Name": "ModelVersion", "Value": model_version}]
    cw.put_metric_data(
        Namespace=NAMESPACE,
        MetricData=[
            {
                "MetricName": "Accuracy",
                "Value": accuracy,
                "Unit": "None",
                "Dimensions": dimensions,
            },
            {
                "MetricName": "CorrectCount",
                "Value": correct,
                "Unit": "Count",
                "Dimensions": dimensions,
            },
            {
                "MetricName": "TotalCount",
                "Value": total,
                "Unit": "Count",
                "Dimensions": dimensions,
            },
        ],
    )

    now = datetime.now()
    result = {
        "timestamp": now.isoformat(),
        "model_version": model_version,
        "total": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
    }
    key = f"eval-results/{now.strftime('%Y%m%d_%H%M')}_{model_version}.json"
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=json.dumps(result, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )

    return accuracy, correct, total


def main():
    parser = argparse.ArgumentParser(description="LPRNet 평가 자동화")
    parser.add_argument("--endpoint", required=True, help="NLB 엔드포인트 (예: http://<NLB_URL>)")
    parser.add_argument("--img_dir", required=True, help="test 이미지 디렉터리")
    parser.add_argument("--model_version", required=True, help="모델 버전 (예: v1.0)")
    args = parser.parse_args()

    accuracy, correct, total = run_evaluation(
        endpoint=args.endpoint.rstrip("/"),
        img_dir=args.img_dir,
        model_version=args.model_version,
    )

    print(f"\n총 {total}장 | 정답 {correct}장 | 정확도: {accuracy * 100:.2f}%")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"accuracy={accuracy:.4f}\n")
            f.write(f"correct={correct}\n")
            f.write(f"total={total}\n")


if __name__ == "__main__":
    main()
