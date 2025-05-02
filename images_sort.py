import os
from PIL import Image

# フォルダパス
input_folder = "saved_images"
output_folder = "saved_images_renamed"

# 出力フォルダを作成
os.makedirs(output_folder, exist_ok=True)

def remove_color(image_path, target_color_hex, tolerance=0):
    img = Image.open(image_path).convert("RGBA")
    datas = img.getdata()

    # hex → RGB 変換
    target_color = tuple(int(target_color_hex[i:i+2], 16) for i in (1, 3, 5))

    new_data = []
    for pixel in datas:
        r, g, b, a = pixel
        # 色の一致判定（許容範囲つき）
        if abs(r - target_color[0]) <= tolerance and \
           abs(g - target_color[1]) <= tolerance and \
           abs(b - target_color[2]) <= tolerance:
            new_data.append((r, g, b, 0))  # alpha を 0 にして透過
        else:
            new_data.append(pixel)

    img.putdata(new_data)
    return img

for file in os.listdir(input_folder):
    if file.endswith(".png"):
        file_path = os.path.join(input_folder, file)
        output_image = remove_color(file_path, "#CBCBCB", tolerance=3)
        output_image.save(file_path)

# A~Z、a~z、および0~9の画像を処理
for filename in os.listdir(input_folder):
    if filename.startswith("uppercase_"):
        char = filename[len("uppercase_"):-4]  # "uppercase_A.png" -> "A"
        new_name = f"{ord(char):04X}.png"      # "A" -> "0041.png"
    elif filename.startswith("lowercase_"):
        char = filename[len("lowercase_"):-4]  # "lowercase_a.png" -> "a"
        new_name = f"{ord(char):04X}.png"      # "a" -> "0061.png"
    elif filename.startswith("hiragana_"):
        char = filename[len("hiragana_"):-4]
        new_name = f"{ord(char):04X}.png"
    elif filename.startswith("katakana_"):
        char = filename[len("katakana_"):-4]
        new_name = f"{ord(char):04X}.png"
    elif filename.startswith("numbers_"):
        char = filename[len("numbers_"):-4]      # "numbers_0.png" -> "0"
        if char.isdigit():
            new_name = f"{ord('0') + int(char):04X}.png"  # "0" -> "0030.png", "1" -> "0031.png", ...
        else:
            print(f"Skipping invalid numbers file: {filename}")
            continue
    else:
        print(f"Skipping unknown file: {filename}")
        continue

    old_path = os.path.join(input_folder, filename)
    new_path = os.path.join(output_folder, new_name)

    if os.path.exists(old_path):
        # 画像を開いてサイズ変更
        with Image.open(old_path) as img:
            resized_img = img.resize((2000, 2000))
            resized_img.save(new_path)
        print(f"Renamed and resized: {filename} -> {new_name}")
    else:
        print(f"File not found: {filename}")