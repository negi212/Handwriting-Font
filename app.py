from flask import Flask, render_template, request
import base64
import os
import socket
import qrcode
import threading
import signal

app = Flask(__name__)

SAVE_FOLDER = 'saved_images'
os.makedirs(SAVE_FOLDER, exist_ok=True)

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
    os.kill(os.getpid(), signal.SIGINT)  # Flaskサーバーを終了
    return "サーバーを終了しました。"

def show_qr():
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

if __name__ == '__main__':
    # QRコード表示を別スレッドで実行
    threading.Thread(target=show_qr).start()

    # Flaskアプリ起動
    app.run(host='0.0.0.0', port=5000, debug=True)
