# num_img = 161 | 예상 생성량: 27 × 161 = 4,347장 → result2/
import os
import random
import uuid

import cv2
import numpy as np


class ImageGenerator:
    def __init__(self, save_dir, plates_dir, nums_dir, chars_dir):
        self.save_dir = save_dir
        self.plates_dir = plates_dir

        # create directories to save images and labels
        for name in "labels", "images":
            os.makedirs(os.path.join(self.save_dir, name), exist_ok=True)

        # load number
        self.numbers = []
        self.number_list = []
        for filename in sorted(os.listdir(nums_dir)):
            img = cv2.imread(os.path.join(nums_dir, filename))
            self.numbers.append(img)
            self.number_list.append(filename.split(".")[0])

        # load character
        self.char_list = []
        self.chars = []
        for filename in os.listdir(chars_dir):
            img = cv2.imread(os.path.join(chars_dir, filename))
            self.chars.append(img)
            self.char_list.append(filename.split(".")[0])
            
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

    @staticmethod
    def add(plate, char):
        # ✅ plate와 char의 크기가 다르면 char 크기를 plate에 맞춰 조정
        if plate.shape[:2] != char.shape[:2]:
            char = cv2.resize(char, (plate.shape[1], plate.shape[0]))

        # ✅ char를 GRAY로 변환 → 마스크 생성
        img2gray = cv2.cvtColor(char, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)

        # ✅ 마스크 크기가 plate와 다를 경우, 크기 맞춰주기
        if mask.shape != plate.shape[:2]:
            mask = cv2.resize(mask, (plate.shape[1], plate.shape[0]))
            mask_inv = cv2.bitwise_not(mask)

        # ✅ 마스크 타입 보정
        mask = mask.astype("uint8")
        mask_inv = mask_inv.astype("uint8")

        # ✅ 실제 합성
        img1 = cv2.bitwise_and(plate, plate, mask=mask)
        img2 = cv2.bitwise_and(char, char, mask=mask_inv)
        output = cv2.add(img1, img2)

        return output

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

    def write_yolo_label(self, file, label, x1, y1, x2, y2, img_w, img_h):
        x_center = (x1 + x2) / 2 / img_w
        y_center = (y1 + y2) / 2 / img_h
        w_norm = (x2 - x1) / img_w
        h_norm = (y2 - y1) / img_h
        class_id = names.index(label)
        file.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")
        
    def get_korean_plate_name(self, plate_content):
        """
        영문으로 표시된 한글 문자를 실제 한글로 변환하여 번호판 이름 생성
        """
        plate_name = ""
        i = 0
        while i < len(plate_content):
            # 한글 문자 처리 (영문 -> 한글 변환)
            if plate_content[i] in self.char_mapping:
                plate_name += self.char_mapping[plate_content[i]]
            else:
                # 숫자 처리
                plate_name += plate_content[i]
            i += 1
        return plate_name

    def type_a(self, num):
        count = 0
        for p in os.listdir(self.plates_dir):
            plate_path = os.path.join(self.plates_dir, p)
            plate = cv2.imread(plate_path)

            if plate is None:
                print(f"❌ 이미지 로드 실패: {plate_path}")
                continue

            # ✅ plate 종류에 따라 크기 조절
            if p == "plate_21.jpg":
                number_size = (40, 80)
                char_size = (50, 65)
            else:
                number_size = (50, 80)
                char_size = (60, 83)

            # ✅ plate 종류별 크기에 따라 글자 resize
            numbers = [cv2.resize(number, number_size) for number in self.numbers]
            chars = [cv2.resize(char, char_size) for char in self.chars]
                
            for i in range(num):
                unique_id = str(uuid.uuid1())
                Plate = cv2.resize(plate.copy(), (520, 110))
                
                # 번호판 내용을 저장할 리스트
                plate_content = []
                
                # ✅ 무작위로 포맷 선택
                is_seven_digit = random.choice([True, False])
                digit_count = 3 if is_seven_digit else 2

                # ✅ 구성: [앞 숫자들] + [한글] + [4자리 숫자]
                front_widths = [56] * digit_count
                hangul_width = [60]
                back_widths = [56] * 4
                widths = front_widths + hangul_width + back_widths

                # ✅ 각 글자 사이 간격 정의
                if p == "plate_21.jpg":
                    gap = 1 if digit_count == 3 else 5  # 반사판은 더 조밀하게
                else:
                    gap = 3 if digit_count == 3 else 7

                # ✅ 추가: 8자리일 때는 전체 폭을 살짝 줄이기
                total_width = sum(widths) + gap * (len(widths) - 1)

                if digit_count == 3:
                    total_width -= 20  # 좌우 padding용 (조절 가능)

                # ✅ 중앙 시작 위치
                col = round((520 - total_width) / 2) - 5

                # ✅ 반사판 번호판이면 오른쪽으로 조금 더 밀기
                if p == "plate_21.jpg":
                    col += 20  # 또는 7 등, 이미지에 따라 조정

                with open(f"{self.save_dir}/labels/{unique_id}.txt", "w") as f:
                    # ✅ 글자 하나씩 그리기
                    for idx, width in enumerate(widths):
                        if idx < digit_count:
                            # 앞 숫자
                            rand_int = random.randint(1, 7) if idx == 0 else random.randint(0, 9)
                            h = number_size[1]
                            row = (110 - h) // 2  # ✅ 세로 가운데 정렬
                            patch = Plate[row:row + h, col:col + width, :]
                            Plate[row:row + h, col:col + width, :] = self.add(patch, self.random_bright(numbers[rand_int]))
                            self.write_yolo_label(f, self.number_list[rand_int], col, row, col + width, row + h, 520, 110)
                            plate_content.append(self.number_list[rand_int])  # 랜덤 인덱스가 아닌 실제 숫자 값을 저장
                        
                        elif idx == digit_count:
                            # 한글
                            char_idx = i % len(chars)
                            h = char_size[1]
                            row = (110 - h) // 2  # ✅ 세로 가운데 정렬
                            patch = Plate[row:row + h, col:col + width, :]
                            Plate[row:row + h, col:col + width, :] = self.add(patch, self.random_bright(chars[char_idx]))
                            self.write_yolo_label(f, self.char_list[char_idx], col, row, col + width, row + h, 520, 110)
                            plate_content.append(self.char_list[char_idx])
                        
                        else:
                            # 뒷자리 숫자
                            rand_int = random.randint(0, 9)
                            h = number_size[1]
                            row = (110 - h) // 2  # ✅ 세로 가운데 정렬
                            patch = Plate[row:row + h, col:col + width, :]
                            Plate[row:row + h, col:col + width, :] = self.add(patch, self.random_bright(numbers[rand_int]))
                            self.write_yolo_label(f, self.number_list[rand_int], col, row, col + width, row + h, 520, 110)
                            plate_content.append(self.number_list[rand_int])  # 랜덤 인덱스가 아닌 실제 숫자 값을 저장

                        col += width + gap
                
                # 번호판 내용을 기반으로 파일명 생성 (영문 -> 한글 변환)
                korean_plate_name = self.get_korean_plate_name(plate_content)
                image_filename = f"{korean_plate_name}.jpg"
                
                # 동일한 파일명이 존재하는 경우 처리
                image_path = os.path.join(self.save_dir, "images", image_filename)
                counter = 1
                while os.path.exists(image_path):
                    image_filename = f"{korean_plate_name}_{counter}.jpg"
                    image_path = os.path.join(self.save_dir, "images", image_filename)
                    counter += 1
                
                cv2.imwrite(image_path, Plate)
                
                # 라벨 파일도 같은 이름으로 저장
                os.rename(
                    os.path.join(self.save_dir, "labels", f"{unique_id}.txt"),
                    os.path.join(self.save_dir, "labels", f"{korean_plate_name}.txt" if counter == 1 else f"{korean_plate_name}_{counter-1}.txt")
                )
                
                count += 1


    def type_b(self, num):
        count = 0
        
        numbers = [cv2.resize(number, (45, 83)) for number in self.numbers]
        chars = [cv2.resize(char, (49, 70)) for char in self.chars]
        
        for p in os.listdir(self.plates_dir):
            plate = cv2.imread(os.path.join(self.plates_dir, p))
            
            if plate is None:
                print(f"❌ 이미지 로드 실패: {p}")
                continue
            
            for i in range(num):
                Plate = cv2.resize(plate.copy(), (355, 155))
                unique_id = str(uuid.uuid1())
                label_path = os.path.join(self.save_dir, "labels", f"{unique_id}.txt")
                
                # 번호판 내용을 저장할 리스트
                plate_content = []
                
                with open(label_path, 'w') as f:
                    row, col = 45, 15  # row + 83, col + 45

                    # number 1
                    x1, y1 = col, row
                    rand_int = random.randint(1, 7)
                    patch = Plate[row:row + 83, col:col + 45, :]
                    Plate[row:row + 83, col:col + 45, :] = self.add(patch, self.random_bright(numbers[rand_int]))

                    x2, y2 = x1 + 45, y1 + 83
                    x_center_norm, y_center_norm = (x1 + x2) / (2 * 355), (y1 + y2) / (2 * 155)
                    width_norm, height_norm = (45 / 355), (83 / 155)

                    cls_idx = names.index(self.number_list[rand_int])
                    f.write(f'{cls_idx} {x_center_norm} {y_center_norm} {width_norm} {height_norm}\n')
                    plate_content.append(self.number_list[rand_int])  # 랜덤 인덱스가 아닌 실제 숫자 값을 저장

                    col += 45
                    x2, y1 = x2, y1
                    # number 2
                    rand_int = random.randint(0, 9)
                    patch = Plate[row:row + 83, col:col + 45, :]
                    Plate[row:row + 83, col:col + 45, :] = self.add(patch, self.random_bright(numbers[rand_int]))

                    x3, y2 = x2 + 45, y2
                    x_center_norm, y_center_norm = (x2 + x3) / (2 * 355), (y1 + y2) / (2 * 155)
                    width_norm, height_norm = (45 / 355), (83 / 155)

                    cls_idx = names.index(self.number_list[rand_int])
                    f.write(f'{cls_idx} {x_center_norm} {y_center_norm} {width_norm} {height_norm}\n')
                    plate_content.append(self.number_list[rand_int])  # 랜덤 인덱스가 아닌 실제 숫자 값을 저장

                    col += 45
                    x3, y1 = x3, y1
                    # number 3
                    char_idx = i % 40
                    Plate[row + 12:row + 82, col + 2:col + 49 + 2, :] = self.add(
                        Plate[row + 12:row + 82, col + 2:col + 49 + 2, :],
                        self.random_bright(chars[char_idx]))

                    x4, y2 = x3 + 49, y2
                    x_center_norm, y_center_norm = (x3 + x4) / (2 * 355), (y1 + y2) / (2 * 155)
                    width_norm, height_norm = (49 / 355), (70 / 155)
                    cls_idx = names.index(self.char_list[char_idx])
                    f.write(f'{cls_idx} {x_center_norm} {y_center_norm} {width_norm} {height_norm}\n')
                    plate_content.append(self.char_list[char_idx])

                    col += 49 + 2
                    x4, y1 = col, y1
                    # numbers 4
                    rand_int = random.randint(0, 9)
                    Plate[row:row + 83, col + 2:col + 45 + 2, :] = self.add(Plate[row:row + 83, col:col + 45, :],
                                                                            self.random_bright(numbers[rand_int]))

                    x5, y2 = x4 + 45 + 2, y2
                    x_center_norm, y_center_norm = (x4 + x5) / (2 * 355), (y1 + y2) / (2 * 155)
                    width_norm, height_norm = (45 / 355), (83 / 155)

                    cls_idx = names.index(self.number_list[rand_int])
                    f.write(f'{cls_idx} {x_center_norm} {y_center_norm} {width_norm} {height_norm}\n')
                    plate_content.append(self.number_list[rand_int])  # 랜덤 인덱스가 아닌 실제 숫자 값을 저장

                    col += 45 + 2
                    x5, y1 = col, y1
                    # number 5
                    rand_int = random.randint(0, 9)
                    Plate[row:row + 83, col:col + 45, :] = self.add(Plate[row:row + 83, col:col + 45, :],
                                                                    self.random_bright(numbers[rand_int]))
                    x6, y2 = x5 + 45, y2
                    x_center_norm, y_center_norm = (x5 + x6) / (2 * 355), (y1 + y2) / (2 * 155)
                    width_norm, height_norm = (45 / 355), (83 / 155)

                    cls_idx = names.index(self.number_list[rand_int])
                    f.write(f'{cls_idx} {x_center_norm} {y_center_norm} {width_norm} {height_norm}\n')
                    plate_content.append(self.number_list[rand_int])  # 랜덤 인덱스가 아닌 실제 숫자 값을 저장

                    col += 45
                    x6, y1 = x6, y1

                    # number 6
                    rand_int = random.randint(0, 9)
                    Plate[row:row + 83, col:col + 45, :] = self.add(Plate[row:row + 83, col:col + 45, :],
                                                                    self.random_bright(numbers[rand_int]))

                    x7, y2 = x6 + 45, y2
                    x_center_norm, y_center_norm = (x6 + x7) / (2 * 355), (y1 + y2) / (2 * 155)
                    width_norm, height_norm = (45 / 355), (83 / 155)

                    cls_idx = names.index(self.number_list[rand_int])
                    f.write(f'{cls_idx} {x_center_norm} {y_center_norm} {width_norm} {height_norm}\n')
                    plate_content.append(self.number_list[rand_int])  # 랜덤 인덱스가 아닌 실제 숫자 값을 저장
                    
                    col += 45
                    x7, y1 = x7, y1

                    # number 7
                    rand_int = random.randint(0, 9)
                    Plate[row:row + 83, col:col + 45, :] = self.add(Plate[row:row + 83, col:col + 45, :],
                                                                    self.random_bright(numbers[rand_int]))
                    x8, y2 = x7 + 45, y2
                    x_center_norm, y_center_norm = (x7 + x8) / (2 * 355), (y1 + y2) / (2 * 155)
                    width_norm, height_norm = (45 / 355), (83 / 155)
                    cls_idx = names.index(self.number_list[rand_int])
                    f.write(f'{cls_idx} {x_center_norm} {y_center_norm} {width_norm} {height_norm}\n')
                    plate_content.append(self.number_list[rand_int])  # 랜덤 인덱스가 아닌 실제 숫자 값을 저장
                
                # 번호판 내용을 기반으로 파일명 생성 (영문 -> 한글 변환)
                korean_plate_name = self.get_korean_plate_name(plate_content)
                image_filename = f"{korean_plate_name}.jpg"
                
                # 동일한 파일명이 존재하는 경우 처리
                image_path = os.path.join(self.save_dir, "images", image_filename)
                counter = 1
                while os.path.exists(image_path):
                    image_filename = f"{korean_plate_name}_{counter}.jpg"
                    image_path = os.path.join(self.save_dir, "images", image_filename)
                    counter += 1
                
                cv2.imwrite(image_path, Plate)
                
                # 라벨 파일도 같은 이름으로 저장
                os.rename(
                    label_path,
                    os.path.join(self.save_dir, "labels", f"{korean_plate_name}.txt" if counter == 1 else f"{korean_plate_name}_{counter-1}.txt")
                )
                
                count += 1


if __name__ == '__main__':
    with open('./assets/names.txt', 'r') as file:
        names = [name.strip() for name in file.readlines()]

    if not os.path.exists('./result2'):
        os.mkdir('./result2')
    if not os.path.exists('./result2/images'):
        os.mkdir('./result2/images')
    if not os.path.exists('./result2/labels'):
        os.mkdir('./result2/labels')

    Type_A1 = ImageGenerator(save_dir='./result2/',
                             plates_dir='./assets/plates/type_a',
                             nums_dir='./assets/nums/',
                             chars_dir='./assets/chars/')

    Type_B1 = ImageGenerator(save_dir='./result2/',
                             plates_dir='./assets/plates/type_b',
                             nums_dir='./assets/nums/',
                             chars_dir='./assets/chars/')

    num_img = 161

    Type_A1.type_a(num_img)
    print("Type 1 finish")
    Type_B1.type_b(num_img)
    print("Type 2 finish")