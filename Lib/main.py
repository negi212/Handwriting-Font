import subprocess as sp
import pickle
import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox
import os
from PIL import Image
import shutil
from flask import Flask, render_template, request
import base64
import socket
import qrcode
import threading
import signal
import numpy as np
import svgwrite
from pathlib import Path
from skimage import measure
from skimage.measure import approximate_polygon
from time import sleep

# Flaskアプリの初期化
app = Flask(__name__)

SAVE_FOLDER = 'saved_images'
os.makedirs(SAVE_FOLDER, exist_ok=True)

def shutdown_server():
    os.kill(os.getpid(), signal.SIGINT)
    return "サーバーを終了しました。"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save', methods=['POST'])
def save():
    data = request.form['image']
    char = request.form['char']
    char_type = request.form['charType']

    header, encoded = data.split(",", 1)
    img_data = base64.b64decode(encoded)

    # ファイル名に文字タイプを含める
    filename = os.path.join(SAVE_FOLDER, f'{char_type}_{char}.png')
    with open(filename, 'wb') as f:
        f.write(img_data)

    return f'{char}を保存しました！'

@app.route('/exit', methods=['POST'])
def exit_app():
    print("終了するにはCtrl+Cを入力してください。")
    # messagebox.showinfo("終了", "アプリケーションを終了するにはCtrl+Cを入力してください。")
    return "サーバーを終了しました。"

def show_qr():
    sleep(1)  # Flaskサーバーが起動するまで待機
    # ローカルIPアドレスの取得
    host = socket.gethostname()
    ip = socket.gethostbyname(host)
    url = f"http://{ip}:5000"

    # QRコード生成
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make()
    qr.print_ascii(invert=True)  # ターミナルにQRコードを表示

    print(f"\nURL: {url}")

# フォルダパス
input_folder = "saved_images"
output_folder = "saved_images_renamed"

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

def convert_to_binary(img_path):
    """画像を2値化して返す"""
    img = Image.open(img_path).convert("RGBA")
    binary = Image.new("L", img.size, 255)
    img_array = np.array(img)
    alpha = img_array[:, :, 3]

    # 完全に透明な画像を判定
    if np.all(alpha == 0):
        return None

    binary_array = np.array(binary)
    binary_array[alpha > 0] = 0
    return Image.fromarray(binary_array)

def get_contours_with_hierarchy(binary_img):
    """2値画像から輪郭を階層的に取得"""
    binary_array = np.array(binary_img) == 0
    labeled_array, _ = measure.label(binary_array, connectivity=2, return_num=True)
    contours = []
    
    for region_label in np.unique(labeled_array):
        if region_label == 0:  # 背景部分を無視
            continue
        region = labeled_array == region_label
        region_contours = measure.find_contours(region, 0.5)
        contours.append(region_contours)
    
    return contours

def simplify_contour(contour, tolerance=2.0):
    """
    輪郭を単純化
    :param contour: 元の輪郭
    :param tolerance: 単純化の許容誤差（値が大きいほど単純化される）
    :return: 単純化された輪郭
    """
    return approximate_polygon(contour, tolerance)

def save_as_svg(binary_img, output_path, tolerance=2.0):
    """輪郭をSVG形式で保存"""
    width, height = binary_img.size
    dwg = svgwrite.Drawing(output_path, size=(width, height))

    # 外側の輪郭を保持し、内側の透明部分を除外
    contours_with_hierarchy = get_contours_with_hierarchy(binary_img)

    for region_contours in contours_with_hierarchy:
        path_data = ""
        for i, contour in enumerate(region_contours):
            if len(contour) > 2:
                # 輪郭を単純化
                simplified_contour = simplify_contour(contour, tolerance)

                # 最初の輪郭を塗りつぶし
                if i == 0:
                    path_data += f"M {simplified_contour[0][1]},{simplified_contour[0][0]}"
                    for y, x in simplified_contour[1:]:
                        path_data += f" L {x},{y}"
                    path_data += " Z"
                # 内側の輪郭を穴として処理
                else:
                    path_data += f" M {simplified_contour[0][1]},{simplified_contour[0][0]}"
                    for y, x in simplified_contour[1:]:
                        path_data += f" L {x},{y}"
                    path_data += " Z"

        # SVGにパスを追加（塗りつぶし領域の穴を保持）
        dwg.add(dwg.path(d=path_data, fill="black", stroke="none"))

    dwg.save()

def save_empty_svg(output_path, width, height):
    """空のSVGを保存"""
    dwg = svgwrite.Drawing(output_path, size=(width, height))
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill="white"))
    dwg.save()

def process_folder(input_dir, output_dir, tolerance=2.0):
    """フォルダ内のPNG画像を処理"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for png_file in input_path.glob("*.png"):
        binary_img = convert_to_binary(png_file)

        # 空白の画像の場合
        if binary_img is None:
            svg_file = output_path / f"{png_file.stem}.svg"
            img = Image.open(png_file)
            save_empty_svg(svg_file, *img.size)
            print(f"Empty image: {png_file.name} -> {svg_file.name}")
        else:
            svg_file = output_path / f"{png_file.stem}.svg"
            save_as_svg(binary_img, svg_file, tolerance)
            print(f"Converted: {png_file.name} -> {svg_file.name}")

# Tkinterの初期化
root = tk.Tk()
root.withdraw()  # メインウィンドウを非表示にする

if __name__ == '__main__':
    # フォルダの初期化
    try:
        for file in os.listdir("saved_images"):
            os.remove(f"saved_images/{file}")
    except FileNotFoundError:
        pass

    # フォント名を入力
    font_name = str(simpledialog.askstring("Font Name", "フォント名を入力:"))

    # pickleに書き出し
    if font_name:
        with open("font_name.pkl", "wb") as f:
            pickle.dump(font_name, f)
    # QRコード表示を別スレッドで実行
    threading.Thread(target=show_qr).start()

    # Flaskアプリ起動
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

    # 出力フォルダを作成
    os.makedirs(output_folder, exist_ok=True)

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
    
    process_folder("saved_images_renamed", "handwriting_font_svg", tolerance=3.0)

    command = ["FontForgePortable/App/FontForge/bin/ffpython.exe", "create_font_from_svg.py"]
    proc = sp.Popen(command)
    proc.communicate()

    try:
        shutil.rmtree("saved_images_renamed")
    except FileNotFoundError:
        pass
    try:
        for file in os.listdir("handwriting_font_svg"):
            os.remove(f"handwriting_font_svg/{file}")
    except FileNotFoundError:
        pass

    try:
        os.remove("font_name.pkl")
    except FileNotFoundError:
        pass