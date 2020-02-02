# -*- coding: utf-8 -*-
from flask import Flask, render_template, Response
from Camera import Camera

app = Flask(__name__)

#index.htmlを返す
@app.route('/')
def index():
    return render_template('index.html')

#カメラ映像を配信する
@app.route('/video')
def video():
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

#カメラオブジェクトから静止画を取得する
def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

#カメラスレッドを生成してFlaskを起動する
if __name__ == '__main__':
    threaded=True
    video()
    app.run(host="0.0.0.0",port=80)
