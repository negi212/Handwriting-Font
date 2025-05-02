import os
from PIL import Image
import numpy as np
import svgwrite
from pathlib import Path
from skimage import measure
from skimage.measure import approximate_polygon


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

if __name__ == "__main__":
    # 単純化の許容誤差（値を増やすとさらに単純化）
    process_folder("saved_images_renamed", "handwriting_font_svg", tolerance=3.0)