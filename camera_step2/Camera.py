# -*- coding: utf-8 -*-
import picamera
import picamera.array
import cv2
import time
import datetime
from base_camera import BaseCamera

###################################################
## 定数定義
###################################################
#動画の格納パス
videopath='/home/pi/camera'

class Camera(BaseCamera):
    ###################################################
    ## カメラ処理のメインメソッド
    ###################################################
    @staticmethod
    def frames():
         # カメラ初期化
         with picamera.PiCamera() as camera:
            #カメラ画像を左右左右逆転させる
            camera.vflip = True
            camera.hflip = True
            
            # 解像度の設定
            camera.resolution = (640, 480)
            
            # カメラの画像をリアルタイムで取得するための処理
            with picamera.array.PiRGBArray(camera) as stream:
                #記録用の動画ファイルを開く（時間ごと）
                curstr=datetime.datetime.now().strftime("%Y%m%d_%H")
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter(str(videopath)+'/video_'+curstr+'.avi',fourcc, 20.0, (640,480))
                
                #カメラ映像が落ち着くまで待つ
                time.sleep(2) 
                
                while True: #カメラから画像を取得してファイルに書き込むことを繰り返す
                    # カメラから映像を取得
                    camera.capture(stream, 'bgr', use_video_port=True)
                    
                    #動画を記録
                    nowstr=datetime.datetime.now().strftime("%Y%m%d_%H")
                    
                    #次の時間になったら新たな動画ファイルを切り替え
                    if curstr != nowstr:
                        curstr=nowstr
                        out.release()
                        out = cv2.VideoWriter(str(videopath)+'/video_'+curstr+'.avi',fourcc, 20.0, (640,480))
                    
                    #動画を記録
                    out.write(stream.array)

                    #ライブ配信用に画像を返す
                    yield cv2.imencode('.jpg', stream.array)[1].tobytes()
                    
                    # 結果の画像を表示する
                    #cv2.imshow('camera', stream.array)

                    #キーが押されたら終了
                    if cv2.waitKey(1) < 255:
                        break
                    
                    # カメラから読み込んだ映像を破棄する
                    stream.seek(0)
                    stream.truncate()
                
                # 表示したウィンドウを閉じる
                out.release()
                cv.destroyAllWindows()

#単独起動用
#Camera.frames()

