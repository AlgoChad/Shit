import tensorflow as tf
from PIL import Image
import numpy as np
import cv2 as cv
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow
from PyQt5.uic import loadUi
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sqlite3
import sys
import os
import image

#Constant Values
COLOR = (255, 255, 0)
NO_DETECTION = "No Eyes Detected"
DETECTED = "Eye Detected!"
GREEN = (124, 252, 0)
WHITE = (255, 255, 255)
PINK = (255,106,128)

#AI Paths
EYE_DETECT_PATH = "eye_detect.xml"
CATARACT_DETECT_HAAR = "Cataract_0.xml"
CNN_CATARACT_TYPES = "types.h5"
CNN_CATARACT_STAGES = "stages.h5"

#Database Paths
PATIENTDDB = "Patiends.db"
PATIENTDATADB = "Patient_data.db"



class Haar_Cascade:
    def __init__(self):
        self.eyes = cv.CascadeClassifier(EYE_DETECT_PATH)
        self.cataract = cv.CascadeClassifier(CATARACT_DETECT_HAAR)
    
          
            
class Convolutional_Neural_Networks:
    def __init__(self):
        self.Types = tf.keras.models.load_model(CNN_CATARACT_TYPES)
        self.Stages = tf.keras.models.load_model(CNN_CATARACT_STAGES)
        
            
            
class AI(Convolutional_Neural_Networks, Haar_Cascade):
    def __init__(self):
        Haar_Cascade.__init__(self)
        Convolutional_Neural_Networks.__init__(self)
        
        
    def cataract_detect(self, gray):
        self.cataract = self.cataract.detectMultiScale(gray,1.1, 5)
        if len(self.cataract) > 0:
            return 1
        return 0
        
        
    def cnn_detect(self, image, model):
        im = Image.fromarray(image, "RGB")
        im = im.resize((500, 500))
        im_array = np.array(im)
        im_array = np.expand_dims(im_array, axis = 0)
        
        if model == 0:
            predict = self.Types.predict(im_array)
        else:
            predict = self.Stages.predict(im_array)

        string = str(predict)
        for character in '[]. ':
            string = string.replace(character, '')
            array = list(string)
    
        for i in range(len(array)):
            if array[i] == '1':
                return i
        
        return -1
        
    def eye_detect(self, cascade, frame, detection):
        for (x, y, w, h) in cascade:
            if (w, h) > (120, 120):
                if detection == "Eye Detected!":
                    cv.rectangle(frame, (100, 80), (540, 400), GREEN, 2)
                cv.rectangle(frame, (x, y), (x + w, y + h), COLOR, 2)
            

    
class Database():
    def __init__(self):
        self.db_path_1 = "Patients.db"
        self.db_path_2 = "Patient_data.db"
        self.dbconnection_1 = sqlite3.connect(self.db_path_1)
        self.dbconnection_2 = sqlite3.connect(self.db_path_2)
    
            
    def prepareDBTableMain(self, dbconnection):
        query = """ CREATE TABLE IF NOT EXISTS "Users" (
                        "firstName"    TEXT,
                        "lastName"    TEXT,
                        "age"    INTEGER,
                        "dob"    TEXT,
                        "email"    TEXT,
                            "address"    TEXT
                        );  """
        dbconnection.execute(query)
        dbconnection.commit()
            
        
    def prepareDBTables(self, dbconnection, tableName):
        query = """ CREATE TABLE IF NOT EXISTS "{0}" (
                        "image" BLOB,
                        "cataract" TEXT,
                        "type" TEXT,
                        "maturity" TEXT,
                        "description" TEXT
                        );  """.format(tableName)
        dbconnection.execute(query)
        dbconnection.commit()
        
    
    def insertRowInDB(self,rowData, connection):
        queryStr = '''INSERT INTO Users ("firstName","lastName","age","dob","email","address") VALUES (?,?,?,?,?,?);'''
        connection.execute(queryStr,rowData)
        connection.commit()
        
            
        
class Main(QMainWindow):
    
    def __init__(self):
        super(Main, self).__init__()
        self.artificial_intelligence = AI()
        self._image_counter = 0
        loadUi('Jb.ui', self)
        self.camera()
    
    
    def camera(self):
        self.capture = cv.VideoCapture(0)
        
        self.browse_button.clicked.connect(self.browse)
        self.capture_button.clicked.connect(self.capture_image)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start()


    def update_frame(self):
        _, frame = self.capture.read()
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            
        cv.rectangle(frame, (100, 80), (540, 400), WHITE, 2)
        eye = self.artificial_intelligence.eyes.detectMultiScale(gray,1.1, 5)
            
        if len(eye) > 0:
            self.artificial_intelligence.eye_detect(eye, frame, DETECTED)
            
        self.display_frame(frame, 1)             
        
        
    def display_frame(self, frame, window = 1):  
        qformat = QImage.Format_Indexed8
        if len(frame.shape) == 3:
            if frame.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
                
        outImage = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], qformat)
        outImage = outImage.rgbSwapped()
        
        if window == 1:
            self.imgLabel.setPixmap(QPixmap.fromImage(outImage))
            self.imgLabel.setScaledContents(True)


    def capture_image(self):
        flag, frame= self.capture.read()
        if flag:
            QtWidgets.QApplication.beep()
            frame = frame[80:400, 100:540] #80:400 - 140:650
            path = "temp_image_dir"
            name = "tempfile{}.png".format(self._image_counter) 
            cv.imwrite(os.path.join(path, name), frame)
            self._image_counter += 1        

        save_and_analyze = Save_analyze(os.path.join(path, name))
        save_and_analyze.exec()
    
    
    def browse(self):
        browse = database_browser()
        browse.exec()



class Save_analyze(QDialog):
    def __init__(self, name):
        super(Save_analyze, self).__init__()
        loadUi("save_and_analyze.ui", self)
        self.artificial_intelligence = AI()
        self.save_data_button.clicked.connect(self.save)
        self.loadImage(name)
        
        
    def loadImage(self, name):
        self.image = cv.imread(name, cv.IMREAD_COLOR)
        self.displayImage(self.image)
        self.cataract()
        
        
    def displayImage(self, img):
        qformat = QImage.Format_Indexed8
        if len(img.shape) == 3:
            if img.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
                
        outImage = QImage(img, img.shape[1], img.shape[0], img.strides[0], qformat)
        outImage = outImage.rgbSwapped()
        
        self.imgLabel.setPixmap(QPixmap.fromImage(outImage))
        self.imgLabel.setScaledContents(True)
    
    
    def cataract(self):
        gray = cv.cvtColor(self.image, cv.COLOR_BGR2GRAY)
        result = self.artificial_intelligence.cataract_detect(gray)
        if result == 1:
            self.cataract_type()
            self.cataract_stage()
            self.label_cataract.setText("Cataract: Positive")
        else:
            self.label_cataract.setText("Cataract: Negative")
            
    
    def cataract_type(self):
        result = self.artificial_intelligence.cnn_detect(self.image, 0)
        if result == 0:
            self.label_cataract_type.setText("Type: Cortical Cataract")
        elif result == 1:
            self.label_cataract_type.setText("Type: Nuclear Sclerotic Cataract")
        elif result == 2:
            self.label_cataract_type.setText("Type: Posterior Subcapsular Cataract")
        else:
            self.label_cataract_type.setText("Type: N/A")
                    
        
    def cataract_stage(self):
        result = self.artificial_intelligence.cnn_detect(self.image, 1)
        if result == 0:
            self.label_cataract_stage.setText("Maturity: Immature")
        else:
            self.label_cataract_stage.setText("Maturity: Mature")
            
            
    def save(self):
        save = save_client_data()
        save.exec()
        


class save_client_data(QDialog):
    def __init__(self):
        super(save_client_data, self).__init__()
        loadUi("data_save.ui", self)
        
        
        
class database_browser(QDialog, Database):
    def __init__(self):
        super(database_browser, self).__init__()
        Database.__init__(self)
        loadUi("browser.ui", self)
        self.prepareDBTableMain(self.dbconnection_1)
        self.showTableData(self.dbconnection_1)
        self.delete_data.clicked.connect(self.delete_item)
        

    def delete_item(self):
        content = "SELECT * FROM Users"
        res = self.dbconnection_1.execute(content)
        for row in enumerate(res):
            if row[0] == self.tableWidget.currentRow():
                data = row[1]
                fname = data[0]
                lname = data[1]
                age = data[2]
                birdthday = data[3]
                print(fname, lname, age, birdthday)
                self.dbconnection_1.execute("DELETE FROM Users Where firstName=? and lastName=? and age=?", (fname, lname, age,))
                self.dbconnection_1.commit()
                self.tableWidget.removeRow(self.tableWidget.currentRow())

        
    def showTableData(self, connection):
        result = connection.cursor().execute("""SELECT * FROM Users""")
        for row_number, row_data in enumerate(result):
            self.tableWidget.insertRow(row_number)
            for column_number, column_data in enumerate(row_data):
                item = str(column_data);
                self.tableWidget.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(item))
    


if __name__ == '__main__':
    App = QApplication(sys.argv)
    Window = Main()
    Window.setWindowTitle("Camera")
    Window.show()
    sys.exit(App.exec_())