import os
from argparse import Namespace
from datetime import datetime
import warnings
import yaml
import torch

import lightning as L
from lightning.pytorch.callbacks import (
    EarlyStopping,
    ModelCheckpoint,
    LearningRateMonitor,
    TQDMProgressBar,
)
from lightning.pytorch.loggers import CSVLogger

from lprnet import LPRNet
from lprnet import DataModule

warnings.filterwarnings("ignore")

if __name__ == "__main__":
    with open("config/kor_config.yaml", encoding="utf-8") as f:
        args = Namespace(**yaml.load(f, Loader=yaml.FullLoader))

    args.saving_ckpt += datetime.now().strftime("_%m-%d_%H:%M")

    if not os.path.exists(args.saving_ckpt):
        os.mkdir(args.saving_ckpt)

    print("=" * 40)
    print("[1/4] 설정 로드 완료")
    print(f"  train_dir : {args.train_dir}")
    print(f"  valid_dir : {args.valid_dir}")
    print(f"  batch_size: {args.batch_size}")
    print(f"  lr        : {args.lr}")
    print(f"  ckpt 저장 : {args.saving_ckpt}")
    device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    print(f"  device    : {device_name}")
    print("=" * 40)

    lprn = LPRNet(args)
    if args.pretrained and os.path.exists(args.pretrained):
        lprn.load_state_dict(torch.load(args.pretrained, map_location="cpu", weights_only=True))
        print(f"[2/4] 사전학습 가중치 로드: {args.pretrained}")
    else:
        print("[2/4] 사전학습 가중치 없음 — 랜덤 초기화로 학습")

    # Set Data Modulews
    data_module = DataModule(args)
    print("[3/4] 데이터 로드 완료")

    print("[4/4] 학습 시작")
    print("=" * 40)

    # Set Trainer
    trainer = L.Trainer(
        max_epochs=300,
        callbacks=[
            TQDMProgressBar(),
            ModelCheckpoint(
                dirpath=args.saving_ckpt,
                monitor="val-acc",
                mode="max",
                filename="{epoch:02d}-{val-acc:.3f}",
                verbose=True,
                save_last=True,
                save_top_k=5,
            ),
            EarlyStopping(
                monitor="val-acc",
                mode="max",
                min_delta=0.00,
                patience=30,
                verbose=True,
            ),
            LearningRateMonitor(logging_interval="step"),
        ],
        precision=16,
        accelerator="auto",
        # amp_backend="apex",
        devices=1,
        logger=CSVLogger("logs"),
    )

    trainer.fit(model=lprn, datamodule=data_module)
