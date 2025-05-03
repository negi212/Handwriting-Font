import os
import shutil

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