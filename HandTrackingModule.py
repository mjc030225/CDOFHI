import mediapipe as mp
import cv2
import time




class handDetector():
    def __init__(self,mode=False,maxHands = 2,modelComplexity=1,detectionCon=0.5,trackCon = 0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.modelComplex = modelComplexity
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands,self.modelComplex,self.detectionCon, self.trackCon)
    #mp.solutions.drawing_utils用于绘制
        self.mpDraw = mp.solutions.drawing_utils

    '''手势检测函数'''
    def findHands(self,img,draw=True):

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 这一行代码将图像从BGR格式转换为RGB格式。BGR是OpenCV默认使用的图像格式，而RGB是一种通用图像格式。在显示图像时，将图像转换为RGB格式可能更好地呈现颜色。
        self.results = self.hands.process(imgRGB)
        # print(results.multi_hand_landmarks)

        if self.results.multi_hand_landmarks:  # 如果检测到多个手势
            for handLms in self.results.multi_hand_landmarks:  # 对每只手进行操作
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)  # 绘制每只手的点阵，且相连
        return img

    '''坐标标注函数'''
    def findPosition(self,img,handNo=0,draw=True):#第0号手

        lmList = []
        if self.results.multi_hand_landmarks:
            myHand =self.results.multi_hand_landmarks[handNo]

            for id, lm in enumerate(myHand.landmark):  # id用于获取手点阵的索引（0为手的跟部，4为大拇指），lm获取手的坐标(比例值）
                h, w, c = img.shape  # 图像：高，宽，通道
                cx, cy = int(lm.x * w), int(lm.y * h)#像素坐标
                lmList.append([id,cx,cy])
                #print(id, cx, cy)
                # if id == 4:#实时显示某个手点的索引
                if draw:#点阵中各点画圆
                    cv2.circle(img,(cx,cy),15,(255,0,0),cv2.FILLED)

        return lmList

    """标注所有手的坐标
    def findallPosition(self,img):
        if self.results.multi_hand_landmarks:  # 如果检测到多个手势
            LMlist=[]
            for handLms in self.results.multi_hand_landmarks:  # 对每只手进行
                myHand = self.results.multi_hand_landmarks[handLms]
                lmList=[]
                for id, lm in enumerate(myHand.landmark):  # id用于获取手点阵的索引（0为手的跟部，4为大拇指），lm获取手的坐标(比例值）
                    h, w, c = img.shape  # 图像：高，宽，通道
                    cx, cy = int(lm.x * w), int(lm.y * h)  # 像素坐标
                    lmList.append([id, cx, cy])
            LMlist.append(lmList)
            return LMlist
    """

def main():
    pTime = 0  # 初始时间
    cTime = 0
    cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)
    detector = handDetector()

    while True:
        success, img = cap.read()
        img = cv2.flip(img, 1)#水平镜像
        img = detector.findHands(img)
        lmList=detector.findPosition(img)
        if len(lmList) != 0:
            print(lmList[4])#4是大拇指
        cTime = time.time()  # 返回1970至今的时间戳
        fps = 1 / (cTime - pTime)  # 计算实时帧率
        pTime = cTime
        # 在img上实时显示帧率：坐标：（10,70），字体，比例，颜色，粗细
        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        cv2.imshow("Image", img)
        cv2.waitKey(1)


if __name__ == "__main__":
    main()

