import dlib
import numpy as np
import cv2
import os
import shutil
import time
import logging
import tkinter as tk
from apply import dlib_window
from tkinter import font as tkFont
from PIL import Image, ImageTk
import sys
from PyQt5 import QtCore,QtGui
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import *
from features_extraction_to_csv import main_tranfer
from face_reco_from_camera import Face_Recognizer
# Dlib 正向人脸检测器 / Use frontal face detector of Dlib
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('/data/data_dlib/shape_predictor_68_face_landmarks.dat')

class Face_Register():
    def __init__(self):

        self.current_frame_faces_cnt = 0  # 当前帧中人脸计数器 / cnt for counting faces in current frame
        self.existing_faces_cnt = 0  # 已录入的人脸计数器 / cnt for counting saved faces
        self.ss_cnt = 0  # 录入 person_n 人脸时图片计数器 / cnt for screen shots
        # self.app=QApplication(sys.argv)
        # self.window=dlib_window()
        self._time=QtCore.QTimer(self.window)
        self.is_camera=0
        self.recognizer=Face_Recognizer()
        self.img_input=self.window.imginput
        self.label_cnt_face_in_database=self.window.faces_database
        self.label_fps_info = self.window.fpsinfo
        self.input_name=self.window.name
        self.label_warning=self.window.is_recognize
        self.action_clear=self.window.actionClear_database
        self.input_name_char = ""
        self.show_keypoints=self.window.keypoint_button
        self.is_show_keypoints=0
        self.label_face_cnt=self.window.face_info
        self.log_all = self.window.log_all
        self.save_button=self.window.save
        self.recognize_button=self.window.recognize
        self.extract_button=self.window.extract_feature
        self.path_photos_from_camera = "data/data_faces_from_camera/"
        self.current_face_dir = ""
        self.font = cv2.FONT_ITALIC
        self.output_frame=self.window.img_output
        # Current frame and face ROI position
        self.current_frame = np.ndarray
        self.face_ROI_image = np.ndarray
        self.face_ROI_width_start = 0
        self.face_ROI_height_start = 0
        self.face_ROI_width = 0
        self.face_ROI_height = 0
        self.ww = 0
        self.hh = 0
        
        self.out_of_range_flag = False
        self.face_folder_created_flag = False
        
        # FPS
        self.frame_time = 0
        self.frame_start_time = 0
        self.fps = 0
        self.fps_show = 0
        self.start_time = time.time()

        self.cap = cv2.VideoCapture(  0,cv2.CAP_DSHOW)  # Get video stream from camera
        # self.cap = cv2.VideoCapture("test.mp4")   # Input local video
        self.time_start()
        self.connect_fun()
    
    def recognize_face(self):
        ret,self.current_frame=self.get_frame()
        result,is_get_face=self.recognizer.process(self.current_frame)
        height, width,channel= result.shape
        q_image = QtGui.QImage(result.data, width, height, channel*width, QtGui.QImage.Format.Format_RGB888)
        img_Image=QtGui.QPixmap.fromImage(q_image)
        self.output_frame.setPixmap(img_Image)
        if is_get_face:
            self.log_all.setText("Cannot detect or recognize the faces!!")
        else:
            self.log_all.setText("We can detect the face!!")
        

    def connect_fun(self):
        self.action_clear.triggered.connect(self.GUI_clear_data)
        self._time.timeout.connect(self.process)
        self.save_button.clicked.connect(self.GUI_get_input_name)
        self.extract_button.clicked.connect(main_tranfer)
        self.recognize_button.clicked.connect(self.recognize_face)
        self.show_keypoints.clicked.connect(self.trans_keypoints)
    # 删除之前存的人脸数据文件夹 / Delete old face folders
    def time_start(self):
        self._time.start(20)
    def trans_keypoints(self):
        self.is_show_keypoints=1-self.is_show_keypoints
    def GUI_clear_data(self):
        # 删除之前存的人脸数据文件夹, 删除 "/data_faces_from_camera/person_x/"...
        folders_rd = os.listdir(self.path_photos_from_camera)
        for i in range(len(folders_rd)):
            shutil.rmtree(self.path_photos_from_camera + folders_rd[i])
        if os.path.isfile("data/features_all.csv"):
            os.remove("data/features_all.csv")
        self.label_cnt_face_in_database.setText("0")
        self.existing_faces_cnt = 0
        self.log_all.setText( "Face images and `features_all.csv` removed!")

    def GUI_get_input_name(self):
        self.input_name_char = self.input_name.text()
        if self.input_name_char:
            self.create_face_folder()
            self.save_current_face()
            self.label_cnt_face_in_database.setText(str(self.existing_faces_cnt))

    # 新建保存人脸图像文件和数据 CSV 文件夹 / Mkdir for saving photos and csv
    def pre_work_mkdir(self):
        # 新建文件夹 / Create folders to save face images and csv
        if os.path.isdir(self.path_photos_from_camera):
            pass
        else:
            os.mkdir(self.path_photos_from_camera)

    # 如果有之前录入的人脸, 在之前 person_x 的序号按照 person_x+1 开始录入 / Start from person_x+1
    def check_existing_faces_cnt(self):
        if os.listdir("data/data_faces_from_camera/"):
            # 获取已录入的最后一个人脸序号 / Get the order of latest person
            person_list = os.listdir("data/data_faces_from_camera/")
            person_num_list = []
            for person in person_list:
                person_order = person.split('_')[1].split('_')[0]
                person_num_list.append(int(person_order))
            self.existing_faces_cnt = max(person_num_list)

        # 如果第一次存储或者没有之前录入的人脸, 按照 person_1 开始录入 / Start from person_1
        else:
            self.existing_faces_cnt = 0
        self.label_cnt_face_in_database.setText(str(self.existing_faces_cnt))

    # 更新 FPS / Update FPS of Video stream
    def update_fps(self):
        now = time.time()
        # 每秒刷新 fps / Refresh fps per second
        if str(self.start_time).split(".")[0] != str(now).split(".")[0]:
            self.fps_show = self.fps
        self.start_time = now
        self.frame_time = now - self.frame_start_time
        self.fps = 1.0 / self.frame_time
        self.frame_start_time = now

        self.label_fps_info.setText(str(self.fps.__round__(2)))

    def create_face_folder(self):
        # 新建存储人脸的文件夹 / Create the folders for saving faces
        self.existing_faces_cnt += 1
        if self.input_name_char:
            self.current_face_dir = self.path_photos_from_camera + \
                                    "person_" + str(self.existing_faces_cnt) + "_" + \
                                    self.input_name_char
        else:
            self.current_face_dir = self.path_photos_from_camera + \
                                    "person_" + str(self.existing_faces_cnt)
        os.makedirs(self.current_face_dir)
        self.log_all.setText( "\"" + self.current_face_dir + "/\" created!")
        logging.info("\n%-40s %s", "新建的人脸文件夹 / Create folders:", self.current_face_dir)
        self.ss_cnt = 0  # 将人脸计数器清零 / Clear the cnt of screen shots
        self.face_folder_created_flag = True  # Face folder already created

    def save_current_face(self):
        if self.face_folder_created_flag:
            if self.current_frame_faces_cnt == 1:
                if not self.out_of_range_flag:
                    self.ss_cnt += 1
                    # 根据人脸大小生成空的图像 / Create blank image according to the size of face detected
                    self.face_ROI_image = np.zeros((int(self.face_ROI_height * 2), self.face_ROI_width * 2, 3),
                                                   np.uint8)
                    for ii in range(self.face_ROI_height * 2):
                        for jj in range(self.face_ROI_width * 2):
                            self.face_ROI_image[ii][jj] = self.current_frame[self.face_ROI_height_start - self.hh + ii][
                                self.face_ROI_width_start - self.ww + jj]
                    self.log_all.setText( "\"" + self.current_face_dir + "/img_face_" + str(
                        self.ss_cnt) + ".jpg\"" + " saved!")
                    self.face_ROI_image = cv2.cvtColor(self.face_ROI_image, cv2.COLOR_BGR2RGB)

                    cv2.imwrite(self.current_face_dir + "/img_face_" + str(self.ss_cnt) + ".jpg", self.face_ROI_image)
                    logging.info("%-40s %s/img_face_%s.jpg", "写入本地 / Save into：",
                                 str(self.current_face_dir), str(self.ss_cnt) + ".jpg")
                else:
                    self.log_all.setText("Please do not out of range!")
            else:
                self.log_all.setText("No face in current frame!")
        else:
            self.log_all.setText("Please run step 2!")

    def get_frame(self):
        try:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except:
            print("Error: No video input!!!")
    
        
    # 获取人脸 / Main process of face detection and saving
    def process(self):
        ret, self.current_frame = self.get_frame()
        faces = detector(self.current_frame, 0)
        # Get frame
        if ret:
            self.update_fps()
            self.label_face_cnt.setText(str(len(faces)))
            # 检测到人脸 / Face detected
            if len(faces) != 0:
                # 矩形框 / Show the ROI of faces
                for k, d in enumerate(faces):
                    self.face_ROI_width_start = d.left()
                    self.face_ROI_height_start = d.top()
                    # 计算矩形框大小 / Compute the size of rectangle box
                    self.face_ROI_height = (d.bottom() - d.top())
                    self.face_ROI_width = (d.right() - d.left())
                    self.hh = int(self.face_ROI_height / 2)
                    self.ww = int(self.face_ROI_width / 2)
                    if self.is_show_keypoints:
                        shape=predictor(self.current_frame,d)
                        points=shape.parts()
                        # print(points[0][0])
                        for i in range(len(points)):
                            cv2.circle(self.current_frame,(points[i].x,points[i].y),radius=2,color=(255,0,0))
                            # cv2.putText(self.current_frame,str(i+1),(points[i].x+1,points[i].y+1),)

                    # 判断人脸矩形框是否超出 480x640 / If the size of ROI > 480x640
                    if (d.right() + self.ww) > 700 or (d.bottom() + self.hh > 520) or (d.left() - self.ww < 0) or (
                            d.top() - self.hh < 0):
                        self.label_warning.setText("OUT OF RANGE!")
                        self.out_of_range_flag = True
                        color_rectangle = (255, 0, 0)
                    else:
                        self.out_of_range_flag = False
                        self.label_warning.setText("GET THE PROPER FACE!")
                        color_rectangle = (255, 255, 255)
                    self.current_frame = cv2.rectangle(self.current_frame,
                                                       tuple([d.left() - self.ww, d.top() - self.hh]),
                                                       tuple([d.right() + self.ww, d.bottom() + self.hh]),
                                                       color_rectangle, 2)
            self.current_frame_faces_cnt = len(faces)


            height, width,channel= self.current_frame.shape
            q_image = QtGui.QImage(self.current_frame.data, width, height, channel*width, QtGui.QImage.Format.Format_RGB888)
            img_Image=QtGui.QPixmap.fromImage(q_image)
            self.img_input.setPixmap(img_Image)




    def run(self):
        self.pre_work_mkdir()
        self.check_existing_faces_cnt()
        self.window.show()
        self.process()
        sys.exit(self.app.exec_())


def main():
    logging.basicConfig(level=logging.INFO)
    Face_Register_con = Face_Register()
    Face_Register_con.run()


if __name__ == '__main__':
    main()
