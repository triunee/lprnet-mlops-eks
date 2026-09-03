import argparse
import torch
import yaml
from argparse import Namespace
from pathlib import Path

from lprnet import LPRNet


def load_model(ckpt_path: str, config_path: str) -> LPRNet:
    ckpt_path = Path(ckpt_path)

    if ckpt_path.suffix == ".ckpt":
        # Lightning 학습 체크포인트
        model = LPRNet.load_from_checkpoint(str(ckpt_path))
    else:
        # 원본 lprnet_kor.pt 형태 (flat state_dict)
        with open(config_path, encoding="utf-8") as f:
            args = Namespace(**yaml.safe_load(f))
        model = LPRNet(args)
        model.load_state_dict(torch.load(str(ckpt_path), map_location="cpu", weights_only=True))

    model.eval()
    return model


def export(ckpt_path: str, output_path: str, config_path: str):
    print(f"체크포인트 로드: {ckpt_path}")
    model = load_model(ckpt_path, config_path)

    # 입력 shape: (batch, channel, height, width) = (1, 3, 50, 100)
    dummy_input = torch.randn(1, 3, 50, 100)

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        opset_version=12,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input":  {0: "batch_size"},
            "output": {0: "batch_size"},
        },
    )
    print(f"ONNX 저장 완료: {output_path}")

    # 변환 검증
    try:
        import onnxruntime as ort
        import numpy as np

        sess = ort.InferenceSession(output_path)
        dummy_np = dummy_input.numpy()
        result = sess.run(["output"], {"input": dummy_np})
        print(f"ONNX 추론 검증 완료 — output shape: {result[0].shape}")
    except ImportError:
        print("onnxruntime 미설치 — 검증 생략 (pip install onnxruntime)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt",   required=True, help="체크포인트 경로 (.ckpt 또는 .pt)")
    parser.add_argument("--output", default="lprnet_kor.onnx", help="출력 ONNX 파일명")
    parser.add_argument("--config", default="config/kor_config.yaml", help="설정 파일 경로")
    args = parser.parse_args()

    export(args.ckpt, args.output, args.config)
