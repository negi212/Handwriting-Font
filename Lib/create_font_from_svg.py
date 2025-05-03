import fontforge
import os
import pickle

def create_font_from_svg(svg_dir, metadata, output_path):
    font_info = metadata['font_info']

    font = fontforge.font()
    font.fontname = font_info['font_name']
    font.familyname = font_info['family_name']
    font.fullname = font_info['full_name']
    font.encoding = "UnicodeFull"

    # フォントメトリクスの設定
    em_size_font = font_info['em_size']
    ascent_image = font_info['ascent']
    descent_image = font_info['descent']
    baseline_y = font_info['baseline_y']

    # スケーリングファクタの計算
    scale = em_size_font / font_info['em_size']

    # フォントメトリクスの設定
    font.ascent = int(ascent_image * scale)
    font.descent = int(descent_image * scale)
    font.em = em_size_font

    print(f"Font metrics set to: ascent={font.ascent}, descent={font.descent}, em_size={font.em}")
    print(f"Scale factor: {scale}")

    os.makedirs(output_path, exist_ok=True)

    # SVGファイルを動的に処理
    for svg_file in [f for f in os.listdir(svg_dir) if f.endswith('.svg')]:
        try:
            unicode_value = int(svg_file.split('.')[0], 16)
            char = chr(unicode_value)

            # 共通の文字パラメータを使用
            char_data = metadata['common_character_data']
            glyph = font.createChar(unicode_value)

            if unicode_value in [0x0020, 0x3000]:
                print(f"スペース文字を処理: U+{unicode_value:04X}")
                if unicode_value == 0x0020:  # 半角スペース
                    glyph.width = em_size_font // 4  # 全角スペースの半分に設定
                elif unicode_value == 0x3000:  # 全角スペース
                    glyph.width = em_size_font  # 全角スペースの幅
                continue

            svg_path = os.path.join(svg_dir, svg_file)
            if os.path.getsize(svg_path) == 0:
                print(f"空白のSVGをスキップ: {svg_file}")
                glyph.width = em_size_font // 2  # 空白幅を適切に設定
                continue

            # Import SVG outlines as vector glyphs
            glyph.importOutlines(svg_path)

            # メタデータから位置情報を取得
            x = int(char_data['position']['x'] * scale)
            y = int(char_data['position']['y'] * scale)
            text_height = int(char_data['text_height'] * scale)

            # フォント座標系への変換
            baseline_image = int(char_data['metrics']['baseline'] * scale)
            vertical_offset = int(char_data['position']['vertical_offset'] * scale * 2)
            y_transform = (font.ascent - baseline_image - baseline_y) + vertical_offset

            # グリフの位置調整を有効化
            glyph.transform((1.0, 0, 0, 1.0, x, y_transform))

            # 幅設定およびサイドベアリング
            glyph.width = em_size_font // 10  # 全体の幅をさらに狭める
            glyph.left_side_bearing = int(x // 8)  # 左側ベアリングをさらに縮小
            glyph.right_side_bearing = int((em_size_font - (x + (char_data['text_width'] * scale))) // 2)  # 半分に

            # グリフのアウトラインがフォントのem_size内に収まっているか確認
            bbox = glyph.boundingBox()
            glyph_top = bbox[3]
            glyph_bottom = bbox[1]

            if glyph_top > font.ascent:
                print(f"警告: U+{unicode_value:04X} ({char}) のグリフがアセントを超えています。glyph_top={glyph_top}, ascent={font.ascent}")
            if glyph_bottom < -font.descent:
                print(f"警告: U+{unicode_value:04X} ({char}) のグリフがデセントを超えています。glyph_bottom={glyph_bottom}, descent={font.descent}")

            glyph.autoHint()
            print(f"処理完了: U+{unicode_value:04X} ({char})")
        except ValueError as e:
            print(f"エラー発生: {svg_file} - ValueError: {e}")
        except Exception as e:
            print(f"エラー発生: {svg_file} - {e}")

    output_file = os.path.join(output_path, f"{font_info['font_name']}.ttf")
    try:
        font.generate(output_file)
        print(f"フォント生成完了: {output_file}")
    except Exception as e:
        print(f"エラー: フォント生成中にエラーが発生しました。{e}")

if __name__ == "__main__":
    with open("font_name.pkl", "rb") as f:
        font_name = pickle.load(f)

    # 共通の文字パラメータ
    common_character_data = {
        "position": {"x": 0, "y": 0, "vertical_offset": 0},  # グリフの初期位置
        "text_height": 900,  # グリフの高さ（em_sizeに対して90%）
        "text_width": 700,   # グリフの幅（em_sizeに対して70%）
        "metrics": {"baseline": 200}  # ベースラインの位置（descent分を確保）
    }

    metadata = {
        "font_info": {
            "font_name": font_name,
            "family_name": font_name,
            "full_name": font_name + " regular",
            "em_size": 1000,       # フォントの基準サイズ
            "ascent": 800,         # ベースラインから上方向の高さ（em_sizeの80%）
            "descent": 200,        # ベースラインから下方向の高さ（em_sizeの20%）
            "baseline_y": 0        # ベースラインの位置
        },
        "common_character_data": common_character_data
    }

    create_font_from_svg(
        "handwriting_font_svg",
        metadata,
        "../"
    )