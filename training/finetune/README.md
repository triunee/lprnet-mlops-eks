# Fine-tuning Code (미확보)

`train.py`, `lprnet.py` 등 실제 파인튜닝 코드는 별도 리포(`LPRNet-master2`)에 있으며 아직 이 리포로 이식되지 않았습니다.

확보되면 이 폴더에 추가하고, [`../../docs/`](../../docs/)에 관련 설정(`kor_config.yaml`의 `lr`, `batch_size`, `max_epochs=300`, `patience=30` 등)과 함께 문서화할 예정입니다.

현재까지 확인된 학습 설정은 [`../../config/kor_config.yaml`](../../config/kor_config.yaml)과 [`../notebooks/lprnet_kor_finetune_onnx_eval.ipynb`](../notebooks/lprnet_kor_finetune_onnx_eval.ipynb) 참고.
