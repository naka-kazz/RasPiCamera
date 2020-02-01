# -*- coding: utf-8 -*-
import picamera
import picamera.array
import cv2
import time
import datetime
import requests
from base_camera import BaseCamera

###################################################
## 定数定義
###################################################
#動画の格納パス
videopath='/home/pi/camera'
#画像の格納パス
pictpath='/home/pi/camera/picts'
#サーバ通知のURL
url='http://localhost:1880/CameraAction'
#サーバ通知のインターバル(秒)
interval=30
#動体検知の精度
detectSize=1000

###################################################
## グローバル変数
###################################################
#動体検知のための前情報保存用
befImg=None
befTimes=[0,0,0,0,0,0]

class Camera(BaseCamera):
    ###################################################
    ## 動体検知のためのメソッド
    ###################################################
    @staticmethod
    def moveDetect(img):
        global befImg,befTimes

        #入力画像をグレースケールに変換
        grayImg=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        #前画像がない場合、現画像を保存し終了
        if befImg is None:
            befImg = grayImg.copy().astype("float")
            return

        #前画像との差分を取得する
        cv2.accumulateWeighted(grayImg, befImg, 0.00001)
        delta = cv2.absdiff(grayImg, cv2.convertScaleAbs(befImg))
        thresh = cv2.threshold(delta, 50, 255, cv2.THRESH_BINARY)[1]
        image, contours, h = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)        
        
        #画像内の最も大きな差分を求める
        max_area=0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if max_area < area:
                max_area = area;

        #次に備えて画像を保存
        befImg = grayImg.copy().astype("float")
                
        #動体が無かったら終了
        if max_area < detectSize:
            return

        #現在時間を取得
        nowstr=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nowTime=time.time()

        #画像をファイルに保存
        filename=pictpath+"/move_"+nowstr+".jpg"
        cv2.imwrite(filename, img)

        #ログ出力
        print(nowstr+' 動体検知 '+filename+' '+str(max_area))           

        #サーバに通知(一定時間間隔)
        if int(nowTime) - befTimes[0] > interval:
            #検知時間を保存
            befTimes[0]=int(nowTime)
            #サーバ通知
            file=open(filename, 'rb').read()
            files = {'file': ('move'+nowstr+'.jpg', file, 'image/jpeg')}
            params = {'action': 'move','text': '玄関で動体検知！'}
            response = requests.post(url, files=files, data=params)
            #サーバ通知結果をログ出力
            print(nowstr+' サーバ通知 動体 '+str(response.status_code)+':'+str(response.content))
        

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

                    #動体検知メソッドを呼び出す
                    Camera.moveDetect(stream.array)
                    
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

