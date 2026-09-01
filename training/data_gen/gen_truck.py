# num_img = 137 | 예상 생성량: 14 × 137 = 1,918장 → result3/

import os
import random
import cv2
import numpy as np


class ImageGenerator:
    def __init__(self, save_path, plates_path, nums_path, chars_path, regions1, regions2, transparent=False):
        self.save_path = save_path
        # Plate
        self.list_ = os.listdir(plates_path)
        self.plate = plates_path

        # Load Numbers - 수정된 부분
        file_path = nums_path
        file_list = os.listdir(file_path)
        # 파일을 숫자 순서대로 정렬
        file_list = sorted(file_list, key=lambda x: int(x.split('.')[0]))
        self.Number = list()
        self.number_list = list()
        for file_ in file_list:
            img_path = os.path.join(file_path, file_)
            if transparent:
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                trans_mask = img[:, :, 3] == 0
                img[trans_mask] = [255, 255, 255, 255]
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            else:
                img = cv2.imread(img_path)

            self.Number.append(img)
            self.number_list.append(file_[0:-4])
    
        # 디버깅을 위한 코드: 숫자 리스트 순서 확인
        print("숫자 리스트 순서:", self.number_list)

        # Load Chars
        file_path = chars_path
        file_list = os.listdir(file_path)
        self.char_list = list()
        self.Char = list()
        for file_ in file_list:
            img_path = os.path.join(file_path, file_)
            if transparent:
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                trans_mask = img[:, :, 3] == 0
                img[trans_mask] = [255, 255, 255, 255]
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            else:
                img = cv2.imread(img_path)

            self.Char.append(img)
            self.char_list.append(file_[0:-4])

        # Load Regions
        file_path = regions1
        file_list = os.listdir(file_path)

        self.region1_list = list()
        self.Regions1 = list()
        for file_ in file_list:
            img_path = os.path.join(file_path, file_)
            if transparent:
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                trans_mask = img[:, :, 3] == 0
                img[trans_mask] = [255, 255, 255, 255]
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            else:
                img = cv2.imread(img_path)

            self.Regions1.append(img)
            self.region1_list.append(file_[0:-4])

        file_path = regions2
        file_list = os.listdir(file_path)

        self.region2_list = list()
        self.Regions2 = list()
        for file_ in file_list:
            img_path = os.path.join(file_path, file_)
            if transparent:
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                trans_mask = img[:, :, 3] == 0
                img[trans_mask] = [255, 255, 255, 255]
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            else:
                img = cv2.imread(img_path)

            self.Regions2.append(img)
            self.region2_list.append(file_[0:-4])

        # 한글 매핑 딕셔너리 생성
        self.char_mapping = {
            "ga": "가", "na": "나", "da": "다", "ra": "라", "ma": "마",
            "ba": "바", "sa": "사", "a": "아", "ja": "자", "ha": "하",
            "geo": "거", "neo": "너", "deo": "더", "reo": "러", "meo": "머",
            "beo": "버", "seo": "서", "eo": "어", "jeo": "저", "heo": "허",
            "go": "고", "no": "노", "do": "도", "ro": "로", "mo": "모",
            "bo": "보", "so": "소", "o": "오", "jo": "조", "ho": "호",
            "gu": "구", "nu": "누", "du": "두", "ru": "루", "mu": "무",
            "bu": "부", "su": "수", "u": "우", "ju": "주",
            "bae": "배", "gwang": "광", "nam": "남", "je": "제", "cheon": "천",
            "dae": "대", "gang": "강", "se": "세", "gi": "기", "gyeong": "경",
            "san": "산", "jong": "종", "buk": "북", "won": "원", "ul": "울",
            "chung": "충", "in": "인", "jeon": "전"
        }

        # 지역 조합 정의
        self.valid_regions = [
            ("seo", "ul"), ("bu", "san"), ("dae", "gu"), ("in", "cheon"),
            ("gwang", "ju"), ("dae", "jeon"), ("ul", "san"), ("se", "jong"),
            ("gyeong", "gi"), ("gang", "won"), ("chung", "buk"), ("chung", "nam"),
            ("jeon", "buk"), ("jeon", "nam"), ("gyeong", "buk"), ("gyeong", "nam"),
            ("je", "ju")
        ]

    @staticmethod
    def add(background_image, char):
        roi = background_image
        img2gray = cv2.cvtColor(char, cv2.COLOR_BGR2GRAY)
        ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        img1_bg = cv2.bitwise_and(roi, roi, mask=mask)
        img2_fg = cv2.bitwise_and(char, char, mask=mask_inv)
        dst = cv2.add(img1_bg, img2_fg)

        return dst

    @staticmethod
    def create_white_char(char_img):
        """
        검은색 글자 이미지를 흰색 글자로 변환
        """
        # 그레이스케일로 변환
        gray = cv2.cvtColor(char_img, cv2.COLOR_BGR2GRAY)

        # 이진화 - 글자 부분을 추출 (글자는 검은색, 배경은 흰색)
        _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

        # 흰색 이미지 생성 (모든 픽셀이 흰색)
        white_img = np.ones_like(char_img) * 255

        # 마스크를 사용하여 글자 부분만 흰색으로 설정
        for c in range(3):  # BGR 채널에 대해
            white_img[:, :, c] = np.where(binary == 255, 255, 0)  # 글자 부분을 흰색으로

        return white_img

    @staticmethod
    def random_bright(img):
        img = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        img = np.array(img, dtype=np.float64)
        random_bright = .5 + np.random.uniform()
        img[:, :, 2] = img[:, :, 2] * random_bright
        img[:, :, 2][img[:, :, 2] > 255] = 255
        img = np.array(img, dtype=np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_HSV2RGB)

        return img

    def direct_overlay(self, background, text_img, x, y, is_white=False):
        """
        배경 이미지에 텍스트 이미지를 직접 오버레이
        """
        h, w, _ = text_img.shape
        gray = cv2.cvtColor(text_img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        roi = background[y:y+h, x:x+w]

        # 마스크 기반으로 배경과 전경 분리
        bg = cv2.bitwise_and(roi, roi, mask=cv2.bitwise_not(mask))

        # 흰색 또는 검은색 텍스트 생성
        if is_white:
            # 흰색 텍스트 (255, 255, 255)
            fg = np.zeros_like(text_img)
            fg[mask > 0] = [255, 255, 255]
        else:
            # 검은색 텍스트 (원본 사용)
            fg = cv2.bitwise_and(text_img, text_img, mask=mask)

        # 배경과 텍스트 합치기
        combined = cv2.add(bg, fg)
        background[y:y+h, x:x+w] = combined

        return background

    def get_korean_text(self, text):
        """
        영문으로 된 문자열을 한글로 변환
        """
        korean_text = ""
        for char in text:
            if char in self.char_mapping:
                korean_text += self.char_mapping[char]
            else:
                korean_text += char
        return korean_text

    def Type_C(self, num, save=False):
        number1 = [cv2.resize(number, (44, 60)) for number in self.Number]
        number2 = [cv2.resize(number, (64, 90)) for number in self.Number]
        region_1 = [cv2.resize(region, (44, 60)) for region in self.Regions1]
        region_2 = [cv2.resize(region, (44, 60)) for region in self.Regions2]
        char = [cv2.resize(char1, (64, 62)) for char1 in self.Char]

        count = 0

        # 유효한 지역 조합 인덱스를 찾기
        region_mapping = {}
        for r1_name, r2_name in self.valid_regions:
            r1_idx = None
            r2_idx = None
            for i, name in enumerate(self.region1_list):
                if name.endswith(r1_name):
                    r1_idx = i
                    break
            for i, name in enumerate(self.region2_list):
                if name.endswith(r2_name):
                    r2_idx = i
                    break
            
            if r1_idx is not None and r2_idx is not None:
                region_mapping[(r1_name, r2_name)] = (r1_idx, r2_idx)

        valid_region_pairs = list(region_mapping.values())

        for p in self.list_:
            plate_path = os.path.join(self.plate, p)
            plate = cv2.imread(plate_path)

            if plate is None:
                print(f"[Type_C] 이미지 불러오기 실패: {plate_path}")
                continue

            # 초록색 번호판 확인 (plate_11.jpg 또는 plate_12.jpg)
            is_green_plate = "plate_11.jpg" in plate_path or "plate_12.jpg" in plate_path

            for i in range(num):
                Plate = cv2.resize(plate, (335, 170))
                plate_content = []  # 번호판 내용을 저장할 리스트
                row, col = 8, 76

                # 유효한 지역 조합 선택
                if valid_region_pairs:
                    region_pair_idx = i % len(valid_region_pairs)
                    r1_idx, r2_idx = valid_region_pairs[region_pair_idx]
                else:
                    # 유효한 조합이 없는 경우 임의 선택 (기존 코드 방식)
                    r1_idx = i % len(self.Regions1)
                    r2_idx = i % len(self.Regions2)

                # region1
                region1_text = self.region1_list[r1_idx][4:]
                plate_content.append(region1_text)

                # region2
                region2_text = self.region2_list[r2_idx][4:]
                plate_content.append(region2_text)

                # 숫자1 (80~97)
                # number1은 8 또는 9만 가능
                first_digit = random.randint(8, 9)
                
                # number1이 9일 경우 number2는 0~7까지만, 8일 경우 0~9까지 가능
                if first_digit == 9:
                    second_digit = random.randint(0, 7)  # 90~97
                else:  # first_digit == 8
                    second_digit = random.randint(0, 9)  # 80~89
                
                # 숫자 이미지 인덱스 (0~9 범위의 인덱스 사용)
                # plate_content에는 실제 번호를 문자열로 저장
                plate_content.append(str(first_digit))
                plate_content.append(str(second_digit))

                # 문자
                c_idx = i % len(char)
                char_text = self.char_list[c_idx]
                plate_content.append(char_text)

                # 숫자2 (4개)
                rand_values = []
                for _ in range(4):
                    rand = random.randint(0, 9)
                    rand_values.append(rand)
                    plate_content.append(self.number_list[rand])

                # 영문 -> 한글 변환하여 파일 이름 생성
                korean_plate_name = ""
                for item in plate_content:
                    if item in self.char_mapping:
                        korean_plate_name += self.char_mapping[item]
                    else:
                        korean_plate_name += item

                # 파일 경로 생성
                label_path = f'./result3/labels/{korean_plate_name}.txt'
                image_path = f'{self.save_path}{korean_plate_name}.jpg'

                # 중복 파일 처리
                counter = 1
                while os.path.exists(image_path):
                    image_path = f'{self.save_path}{korean_plate_name}_{counter}.jpg'
                    label_path = f'./result3/labels/{korean_plate_name}_{counter}.txt'
                    counter += 1

                with open(label_path, 'w') as f:
                    # region1
                    if is_green_plate:
                        # 초록색 번호판에는 직접 흰색 텍스트 오버레이
                        self.direct_overlay(Plate, region_1[r1_idx], col, row, is_white=True)
                    else:
                        # 노란색 번호판에는 기존 방식 사용
                        Plate[row:row+60, col:col+44, :] = self.add(Plate[row:row+60, col:col+44, :],
                                                                self.random_bright(region_1[r1_idx]))

                    x1, y1 = col, row
                    x2 = col + 44
                    f.write(f'{names.index(self.region1_list[r1_idx][4:])} {(x1+x2)/670:.6f} {(y1+row+60)/340:.6f} {44/335:.6f} {60/170:.6f}\n')
                    col += 44

                    # region2
                    if is_green_plate:
                        # 초록색 번호판에는 직접 흰색 텍스트 오버레이
                        self.direct_overlay(Plate, region_2[r2_idx], col, row, is_white=True)
                    else:
                        # 노란색 번호판에는 기존 방식 사용
                        Plate[row:row+60, col:col+44, :] = self.add(Plate[row:row+60, col:col+44, :],
                                                                self.random_bright(region_2[r2_idx]))

                    x1 = col
                    x2 = col + 44
                    f.write(f'{names.index(self.region2_list[r2_idx][4:])} {(x1+x2)/670:.6f} {(y1+row+60)/340:.6f} {44/335:.6f} {60/170:.6f}\n')
                    col += 44 + 8

                    # number1 (80~97)
                    # 첫 번째 숫자 (8 또는 9)
                    if is_green_plate:
                        # first_digit은 8 또는 9이므로 self.Number 리스트에서 해당 인덱스 사용
                        first_digit_idx = int(first_digit)  # 숫자 값을 정수로 변환하여 인덱스로 사용
                        self.direct_overlay(Plate, number1[first_digit_idx], col, row, is_white=True)
                    else:
                        # 노란색 번호판에는 기존 방식 사용
                        first_digit_idx = int(first_digit)
                        Plate[row:row+60, col:col+44, :] = self.add(Plate[row:row+60, col:col+44, :],
                                                            self.random_bright(number1[first_digit_idx]))

                    x1 = col
                    x2 = col + 44
                    f.write(f'{names.index(str(first_digit))} {(x1+x2)/670:.6f} {(y1+row+60)/340:.6f} {44/335:.6f} {60/170:.6f}\n')
                    col += 44

                    # 두 번째 숫자 (0-9 또는 0-7)
                    if is_green_plate:
                        second_digit_idx = int(second_digit)  # 숫자 값을 정수로 변환하여 인덱스로 사용
                        self.direct_overlay(Plate, number1[second_digit_idx], col, row, is_white=True)
                    else:
                        second_digit_idx = int(second_digit)
                        Plate[row:row+60, col:col+44, :] = self.add(Plate[row:row+60, col:col+44, :],
                                                            self.random_bright(number1[second_digit_idx]))

                    x1 = col
                    x2 = col + 44
                    f.write(f'{names.index(str(second_digit))} {(x1+x2)/670:.6f} {(y1+row+60)/340:.6f} {44/335:.6f} {60/170:.6f}\n')
                    col += 44

                    # 아래 행 (row2)
                    row, col = 72, 8

                with open(label_path, 'a') as f:
                    # char
                    if is_green_plate:
                        # 초록색 번호판에는 직접 흰색 텍스트 오버레이
                        self.direct_overlay(Plate, char[c_idx], col, row, is_white=True)
                    else:
                        # 노란색 번호판에는 기존 방식 사용
                        Plate[row:row+62, col:col+64, :] = self.add(Plate[row:row+62, col:col+64, :],
                                                                self.random_bright(char[c_idx]))

                    x1 = col
                    x2 = col + 64
                    f.write(f'{names.index(self.char_list[c_idx])} {(x1+x2)/670:.6f} {(row+row+62)/340:.6f} {64/335:.6f} {62/170:.6f}\n')
                    col += 64

                    # number2 (4개) - 이미 생성한 rand_values 사용
                    for k in range(4):
                        rand = rand_values[k]

                        if is_green_plate:
                            # 초록색 번호판에는 직접 흰색 텍스트 오버레이
                            self.direct_overlay(Plate, number2[rand], col, row, is_white=True)
                        else:
                            # 노란색 번호판에는 기존 방식 사용
                            Plate[row:row+90, col:col+64, :] = self.add(Plate[row:row+90, col:col+64, :],
                                                                    self.random_bright(number2[rand]))

                        x1 = col
                        x2 = col + 64
                        f.write(f'{names.index(self.number_list[rand])} {(x1+x2)/670:.6f} {(row+row+90)/340:.6f} {64/335:.6f} {90/170:.6f}\n')
                        col += 64

                # 모든 번호판 유형에 대해 밝기 조절 적용
                Plate = self.random_bright(Plate)

                if save:
                    cv2.imwrite(image_path, Plate)
                else:
                    cv2.imshow(korean_plate_name, Plate)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()

                count += 1

    def Type_D(self, num, save=False):
        number = [cv2.resize(number, (56, 83)) for number in self.Number]
        char = [cv2.resize(char, (60, 83)) for char in self.Char]
        region_1 = [cv2.resize(region, (60, 42)) for region in self.Regions1]
        region_2 = [cv2.resize(region, (60, 42)) for region in self.Regions2]
        count_d = 0

        # 유효한 지역 조합 인덱스를 찾기
        region_mapping = {}
        for r1_name, r2_name in self.valid_regions:
            r1_idx = None
            r2_idx = None
            for i, name in enumerate(self.region1_list):
                if name.endswith(r1_name):
                    r1_idx = i
                    break
            for i, name in enumerate(self.region2_list):
                if name.endswith(r2_name):
                    r2_idx = i
                    break
            
            if r1_idx is not None and r2_idx is not None:
                region_mapping[(r1_name, r2_name)] = (r1_idx, r2_idx)

        valid_region_pairs = list(region_mapping.values())

        for p in self.list_:
            plate = cv2.imread(os.path.join(self.plate, p))

            if plate is None:
                continue

            for i in range(num):
                # 번호판 내용을 저장할 리스트
                plate_content = []
                Plate = cv2.resize(plate, (520, 110))

                # 유효한 지역 조합 선택
                if valid_region_pairs:
                    region_pair_idx = i % len(valid_region_pairs)
                    region1_idx, region2_idx = valid_region_pairs[region_pair_idx]
                else:
                    # 유효한 조합이 없는 경우 임의 선택 (기존 코드 방식)
                    region1_idx = i % 16
                    region2_idx = i % 16

                # 지역 코드
                plate_content.append(self.region1_list[region1_idx][4:])
                plate_content.append(self.region2_list[region2_idx][4:])

                # 번호 1과 2 - 80~97 범위 생성
                # number1은 8 또는 9만 가능
                first_digit = random.randint(8, 9)
                
                # number1이 9일 경우 number2는 0~7까지만, 8일 경우 0~9까지 가능
                if first_digit == 9:
                    second_digit = random.randint(0, 7)  # 90~97
                else:  # first_digit == 8
                    second_digit = random.randint(0, 9)  # 80~89
                
                # 숫자 이미지 인덱스 (0~9 범위의 인덱스 사용)
                # plate_content에는 실제 번호를 문자열로 저장
                plate_content.append(str(first_digit))
                plate_content.append(str(second_digit))

                # 문자
                char_idx = i % 5
                plate_content.append(self.char_list[char_idx])

                # 나머지 번호들 - 미리 생성하고 플레이트 콘텐츠에 추가
                rand_ints = [random.randint(0, 9) for _ in range(4)]
                for rand in rand_ints:
                    plate_content.append(self.number_list[rand])

                # 영문 -> 한글 변환하여 파일 이름 생성
                korean_plate_name = ""
                for item in plate_content:
                    if item in self.char_mapping:
                        korean_plate_name += self.char_mapping[item]
                    else:
                        korean_plate_name += item

                # 파일 경로 생성
                label_path = f'./result3/labels/{korean_plate_name}.txt'
                image_path = f'{self.save_path}{korean_plate_name}.jpg'

                # 중복 파일 처리
                counter = 1
                while os.path.exists(image_path):
                    image_path = f'{self.save_path}{korean_plate_name}_{counter}.jpg'
                    label_path = f'./result3/labels/{korean_plate_name}_{counter}.txt'
                    counter += 1

                with open(label_path, 'w') as f:
                    row, col = 13, 25
                    x_0, y_0 = 25, 13

                    # region 1
                    Plate[row:row + 42, col:col + 60, :] = self.add(Plate[row:row + 42, col:col + 60, :],
                                                                self.random_bright(region_1[region1_idx]))

                    x_1, y_1 = x_0 + 60, y_0 + 42
                    x_r, y_r = (x_0 + x_1) / (2 * 520), (y_0 + y_1) / (2 * 110)
                    w_r, h_r = (60 / 520), (42 / 110)
                    class_name = names.index(self.region1_list[region1_idx][4:])
                    f.write(f'{class_name} {x_r} {y_r} {w_r} {h_r}\n')

                    x_2, y_2 = x_0, y_0 + 42

                    # region 2
                    Plate[row + 42:row + 84, col:col + 60, :] = self.add(Plate[row + 42:row + 84, col:col + 60, :],
                                                                    self.random_bright(region_2[region2_idx]))

                    x_3, y_3 = x_1, y_0 + 84

                    x_r, y_r = (x_2 + x_3) / (2 * 520), (y_2 + y_3) / (2 * 110)
                    w_r, h_r = (60 / 520), (42 / 110)
                    class_name = names.index(self.region2_list[region2_idx][4:])
                    f.write(f'{class_name} {x_r} {y_r} {w_r} {h_r}\n')

                    col += 60
                    
                    # number 1 (첫 번째 숫자: 8 또는 9)
                    x1, y1 = col, row
                    first_digit_idx = int(first_digit)  # 숫자 값을 정수로 변환하여 인덱스로 사용
                    Plate[row:row + 83, col:col + 56, :] = self.add(Plate[row:row + 83, col:col + 56, :],
                                                            self.random_bright(number[first_digit_idx]))
                    x2, y2 = x1 + 56, y1 + 83
                    x_r, y_r = (x1 + x2) / (2 * 520), (y1 + y2) / (2 * 110)
                    w_r, h_r = (56 / 520), (83 / 110)
                    class_name = names.index(str(first_digit))
                    f.write(f'{class_name} {x_r} {y_r} {w_r} {h_r}\n')

                    col += 56
                    # number 2 (두 번째 숫자: 0-9 또는 0-7)
                    x1 = col
                    second_digit_idx = int(second_digit)  # 숫자 값을 정수로 변환하여 인덱스로 사용
                    Plate[row:row + 83, col:col + 56, :] = self.add(Plate[row:row + 83, col:col + 56, :],
                                                            self.random_bright(number[second_digit_idx]))
                    x2 = x1 + 56
                    x_r, y_r = (x1 + x2) / (2 * 520), (y1 + y2) / (2 * 110)
                    w_r, h_r = (56 / 520), (83 / 110)
                    class_name = names.index(str(second_digit))
                    f.write(f'{class_name} {x_r} {y_r} {w_r} {h_r}\n')
                    col += 56
                    # character 3
                    x1 = col
                    Plate[row:row + 83, col:col + 60, :] = self.add(Plate[row:row + 83, col:col + 60, :],
                                                                self.random_bright(char[char_idx]))
                    x2 = x1 + 60
                    x_r, y_r = (x1 + x2) / (2 * 520), (y1 + y2) / (2 * 110)
                    w_r, h_r = (60 / 520), (83 / 110)
                    class_name = names.index(self.char_list[char_idx])
                    f.write(f'{class_name} {x_r} {y_r} {w_r} {h_r}\n')

                    col += (40 + 36)
                    # numbers 4-7 - 미리 생성한 rand_ints 사용
                    for k in range(4):
                        rand_int = rand_ints[k]
                        x1 = col
                        Plate[row:row + 83, col:col + 56, :] = self.add(Plate[row:row + 83, col:col + 56, :],
                                                                    self.random_bright(number[rand_int]))
                        x2 = col + 56
                        x_r, y_r = (x1 + x2) / (2 * 520), (y1 + y2) / (2 * 110)
                        w_r, h_r = (56 / 520), (83 / 110)
                        class_name = names.index(self.number_list[rand_int])
                        f.write(f'{class_name} {x_r} {y_r} {w_r} {h_r}\n')
                        col += 56

                # 밝기 조정 추가
                Plate = self.random_bright(Plate)

                if save:
                    cv2.imwrite(image_path, Plate)
                    count_d += 1
                else:
                    pass


if __name__ == '__main__':

    with open('./assets/names.txt', 'r') as file:
        names = file.readlines()

    names = [i.strip() for i in names]
    print(names)

    if not os.path.exists('./result3'):
        os.mkdir('./result3')
    if not os.path.exists('./result3/images'):
        os.mkdir('./result3/images')
    if not os.path.exists('./result3/labels'):
        os.mkdir('./result3/labels')

    TruckNP_type_1 = ImageGenerator(save_path='./result3/images/',
                                  plates_path='./assets/plates/type_c',
                                  nums_path='./assets/nums/',
                                  chars_path='./assets/chars_truck/',
                                  regions1='./assets/region1/',
                                  regions2='./assets/region2/')

    TruckNP_type_2 = ImageGenerator(save_path='./result3/images/',
                                  plates_path='./assets/plates/type_d',
                                  nums_path='./assets/nums/',
                                  chars_path='./assets/chars_truck/',
                                  regions1='./assets/region1/',
                                  regions2='./assets/region2/')

    num_img = 137
    TruckNP_type_1.Type_C(num_img, save=True)
    TruckNP_type_2.Type_D(num_img, save=True)