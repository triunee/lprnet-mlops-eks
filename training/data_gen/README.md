# 차량 번호판 이미지 및 라벨 생성

## 📁 구조

```buildoutcfg
├── assets/
│   └── names.txt               # 차량 번호 생성을 위한 이름 리스트
├── character_list.txt         # 전체 character 리스트 (dictionary)
├── generate2.py               # 자동차 정면 이미지 및 라벨 생성
├── generate_truck2.py         # 화물용 정면 이미지 및 라벨 생성 : 7자리, 지역명 포함
├── generate_truck2_8.py         # 화물용 정면 이미지 및 라벨 생성 : 8자리
├── generate_m.py               # 군용차량 정면 이미지 및 라벨 생성
├── transform_images.py        # 이미지 변형 및 라벨 생성
├── dataTransform.py           # 모델 학습용 라벨 포맷 변환 및 train/val 분할
├── getcharacter.py            # 이미지 파일명에서 문자 추출하여 dictionary 생성

```

`assets` folder:

```buildoutcfg
assets
├── chars
    ├── a.jpg
    └── ...
├── chars_truck
    ├── a.jpg
    └── ...
├── chars_m
    ├── guk.jpg
    └── ...
├── nums
    ├── 0.jpg
    └── ...
├── region1
    ├── 001_bu.jpg
    └── ...
├── region2
    ├── 001_san.jpg
    └── ...
└── plates
    ├── type_a
        ├── plate_1jpg
        └── ...
    └── type_b
        ├── plate_1jpg
        └── ...
    └── type_c
        ├── plate_1jpg
        └── ...
    └── type_d
        ├── plate_1jpg
        └── ...
└── names.txt
```
`generate~.py` 실행 후, `result` 폴더:
```buildoutcfg
result
├── images
    ├── 강주00바3571.jpg
    └── ...
└── labels
    ├── 강주00바3571.txt
    └── ...
```

* Labels are prepared according to YOLO labelling format


## 생성 결과
- 자동차 : 화물차(+군용) = 6:4 비율 생성
- 자동차 번호판 생성:
    - 7자리, 8자리, 반사판 유무, 수소차량
    - 기본 + 방향전환 : **58,800 장**
- 화물용 +군용 번호판 비율 기반 생성:
  - 7자리: 75% (**6,300 장**)
  - 8자리: 20% (**1,764 장**)
  - 군용차량: 5% (**432 장**)
  - 기본 + 방향 전환 : **42,480 장**

## 작업 순서

1. **이미지 및 라벨 생성**
   - `generate2.py`, `generate_truck2.py`, `generate_truck2_8.py`, `generate_m.py` 실행
2. **이미지 변형**
   - `transform_images.py` 실행
3. **라벨 포맷 통일 및 분할**
   - `dataTransform.py` 실행


Reference

1. https://github.com/yakhyo/korean-license-plate-generator
2. [https://github.com/qjadud1994/Korean-license-plate-Generator](https://github.com/qjadud1994/Korean-license-plate-Generator)
