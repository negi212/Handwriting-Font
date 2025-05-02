import subprocess as sp
import pickle
import tkinter as tk
from tkinter import simpledialog
import os
import requests

filename = "font_data.zip"
urldata = requests.get().content
with open(filename, mode="wb") as f:
    f.write(urldata)

# フォルダの初期化
try:
    for file in os.listdir("output"):
        os.remove(f"output/{file}")
except FileNotFoundError:
    pass
try:
    for file in os.listdir("saved_images"):
        os.remove(f"saved_images/{file}")
except FileNotFoundError:
    pass

# Tkinterの初期化
root = tk.Tk()
root.withdraw()  # メインウィンドウを非表示にする

# フォント名を入力
font_name = str(simpledialog.askstring("Font Name", "フォント名を入力:"))

# pickleに書き出し
if font_name:
    with open("font_name.pkl", "wb") as f:
        pickle.dump(font_name, f)
code_list = [
    "app.py",
    "images_sort.py",
    "png_to_svg.py",]
for code in code_list:
    command = ["python", code]
    proc = sp.Popen(command)
    proc.communicate()

command = ["ffpython", "create_font_from_svg.py"]
proc = sp.Popen(command)
proc.communicate()

command = ["python", "clean.py"]
proc = sp.Popen(command)
proc.communicate()