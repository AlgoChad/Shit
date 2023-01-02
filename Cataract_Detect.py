import tensorflow as tf
from PIL import Image
import numpy as np
import cv2 as cv
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow
from PyQt5.uic import loadUi
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sqlite3
import sys
import os
from automail import automail
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
PATIENTDDB = "Patients.db"
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
        self.db_path_1 = PATIENTDDB
        self.db_path_2 = PATIENTDATADB
        self.dbconnection_1 = sqlite3.connect(self.db_path_1)
        self.dbconnection_2 = sqlite3.connect(self.db_path_2)
    
            
    def prepareDBTableMain(self, dbconnection):
        query = """ CREATE TABLE IF NOT EXISTS "Users" (
                        "firstName"    TEXT,
                        "lastName"    TEXT,
                        "age"    TEXT,
                        "dob"    TEXT,
                        "gender" TEXT,
                        "email"    TEXT,
                        "address"    TEXT
                        );  """
        dbconnection.execute(query)
        dbconnection.commit()
            
        
    def prepareDBTables(self, dbconnection, table_name):
        query = """ CREATE TABLE IF NOT EXISTS "{0}" (
                        "image" BLOB,
                        "cataract" TEXT,
                        "type" TEXT,
                        "maturity" TEXT,
                        "description" TEXT
                        );  """.format(table_name)
        dbconnection.execute(query)
        dbconnection.commit()
        
    
    def delete_db_table(self, dbconnection, table_name):
        query = """ DROP TABLE IF EXISTS "{0}" """.format(table_name)
        dbconnection.execute(query)
        dbconnection.commit()
        
    
    def insert_into_list(self, patient):
        query_string = '''INSERT INTO Users ("firstName","lastName","age","dob","gender","email","address") 
                            VALUES (?,?,?,?,?,?,?);'''
        self.dbconnection_1.execute(query_string, patient)
        self.dbconnection_1.commit()
        
        
    def insert_analysis(self, captured, analysis, table_name):
        analysis.insert(0, sqlite3.Binary(captured.read()))
        query_string = """INSERT INTO "{0}" ("image", "cataract", "type", "maturity", "descriotion") 
                            values (?,?,?,?,?)""".format(table_name)
        self.dbconnection_2.execute(query_string, analysis)
        self.dbconnection_2.commit()
            
        
class Main(QMainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.artificial_intelligence = AI()
        self._image_counter = 0
        loadUi('Mainwindow.ui', self)
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
            name = "tempfile.png"
            cv.imwrite(os.path.join(path, name), frame)

        print(os.path.join(path, name))
        choice = choices(path, name)
        choice.exec()
    
    def browse(self):
        browse = database_browser(1, None, None)
        browse.exec()



class choices(QDialog):
    def __init__(self, path, name):
        super(choices, self).__init__()
        loadUi("choice.ui", self)
        self.path = path
        self.name = name
        self.browse_existing.clicked.connect(self.call_db_browser)
        self.create_new.clicked.connect(self.new_user)
    
    
    def new_user(self):
        save = save_client_data(self.path, self.name)
        save.exec()
    
        
    def call_db_browser(self):
        browse = database_browser(0, self.path, self.name)
        browse.exec()



class save_analyze(QDialog, Database):
    def __init__(self, name, patient, table_name, email):
        super(save_analyze, self).__init__()
        loadUi("save_and_analyze.ui", self)
        self.artificial_intelligence = AI()
        self.email = email
        self.patient = patient
        self.table_name = table_name
        self.image_name = name
        self.captured = open("temp_image_dir/tempfile.png", "rb")
        self.loadImage(name)
        self.analysis = [self.label_cataract.text(), 
                         self.label_cataract_type.text(),
                         self.label_cataract_stage.text(),
                         self.label_cataract_description.text()]
        self.proceed_button.clicked.connect(self.save)
        self.close_button.clicked.connect(lambda: self.close())
        
        
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
            type = self.cataract_type()
            stage = self.cataract_stage()
            self.cataract_description(type, stage)
            self.label_cataract.setText("Cataract: Positive")
        else:
            self.label_cataract.setText("Cataract: Negative")
            
    
    def cataract_type(self):
        type_list = ["Cortical Cataract",
                     "Nuclear Sclerotic Cataract",
                     "Posterior Subcapsular Cataract"]
        result = self.artificial_intelligence.cnn_detect(self.image, 0)
        if result == 0:
            self.label_cataract_type.setText("Type: {0}". format(type_list[result]))
        elif result == 1:
            self.label_cataract_type.setText("Type: {0}". format(type_list[result]))
        elif result == 2:
            self.label_cataract_type.setText("Type: {0}". format(type_list[result]))
        else:
            self.label_cataract_type.setText("Type: N/A")
        
        return result
        
    def cataract_stage(self):
        stage_list = ["Immature",
                      "Mature",
                      "Hypermature"]
        result = self.artificial_intelligence.cnn_detect(self.image, 1)
        if result == 0:
            self.label_cataract_stage.setText("Stage: {0}".format(stage_list[result]))
        elif result == 1:
            self.label_cataract_stage.setText("Stage: {0}".format(stage_list[result]))
        elif result == 2:
            self.label_cataract_stage.setText("Stage: {0}".format(stage_list[result]))
            
        return result
            
            
    def cataract_description(self, type, stage):
        stage_desc_list = ["Immature cataract: Proteins have started to cloud the lens, making it slightly opaque, especially in the center. At this point, your ophthalmologist would recommend new glasses, anti-glare lenses, and increased attention to the light, such as that needed to read correctly. Progression of an immature cataract can take up to several years.",
                           "Mature cataract: The opaqueness has increased to such a point that it can appear milky and white, or amber in color. It has spread to the edges of the lens and has a considerable effect on vision. At this point, your ophthalmologist would ask you how your quality of life and daily activities are affected. If the cataract seriously affects your life, removal surgery may be recommended. ",
                           "Hypermature cataract: The cataract has become very dense, impairing vision to a significant extent, and has hardened. At this point, it would impair vision to an advanced stage. It can be more difficult to remove. If not treated, hypermature cataracts can cause inflammation in the eye and/or increased pressure within the eye, which can cause glaucoma.  "]
        
        type_desc_list = ["Nuclear Sclerotic: These type of cataract form deep in the nucleus. The yellowing and hardening of the central portion of the crystalline lense occurs slowly over the years.",
                          "Cortical: These cataracts have white opaque (spokes) that start to affect peripheral vision and works towards the center. Progression is variable with some progressing over years and others in months.",
                          "Posterior Subcapsular: Progression is variable but tends to progress more rapidly than nuclear sclerotic cataracts. They affect diabetcis and people whoe use high dosage of steroids."]
    
        self.label_cataract_description.setText("Description: {0}".format("\n" + type_desc_list[type] + "\n" + stage_desc_list[stage]))
            
    def save(self):
        mail = automail()
        if self.patient is None:
            mail.send_mail('\n'.join(self.analysis), self.email)
            self.prepareDBTableMain(self.dbconnection_1)
            self.prepareDBTables(self.dbconnection_2, str(self.table_name))
            self.insert_analysis(self.captured, self.analysis, str(self.table_name))
        else:
            mail.send_mail('\n'.join(self.analysis), self.patient[5])
            self.prepareDBTableMain(self.dbconnection_1)
            self.prepareDBTables(self.dbconnection_2, str(self.table_name))
            self.insert_into_list(self.patient)
            self.insert_analysis(self.captured, self.analysis, str(self.table_name))
        
        
        self.close()


class save_client_data(QDialog):
    def __init__(self, path, name):
        super(save_client_data, self).__init__()
        Database.__init__(self)
        self.path = path
        self.name = name
        loadUi("data_save.ui", self)
        self.save_data_button.clicked.connect(self.save)
        self.save_cancel_button.clicked.connect(lambda: self.close())
        
        
    def save(self):
        self.captured = open("temp_image_dir/tempfile.png", "rb")
        self.patient = [str(self.first_name.toPlainText()), 
                        str(self.last_name.toPlainText()), 
                        str(self.age.toPlainText()), 
                        str(self.birthday_edit.date().toPyDate()), 
                        str(self.gender.currentText()), 
                        str(self.email.toPlainText()), 
                        str(self.address.toPlainText())]
        self.table_name = [str(self.first_name.toPlainText()), 
                            str(self.last_name.toPlainText()), 
                            str(self.age.toPlainText()), 
                            str(self.birthday_edit.date().toPyDate())]
        save_and_analyze = save_analyze(os.path.join(self.path, self.name), self.patient, self.table_name)
        save_and_analyze.exec()
        self.close()
      
        
        
class database_browser(QDialog, Database):
    def __init__(self, window, path, name):
        super(database_browser, self).__init__()
        Database.__init__(self)
        self.name = name
        self.path = path
        if (window == 0):
            loadUi("browser_choice.ui", self)
            self.proceed.clicked.connect(self.proceed_save)
        else:
            loadUi("browser.ui", self)
            self.delete_data.clicked.connect(self.delete_item)
            self.open_data.clicked.connect(self.open_user)
        self.prepareDBTableMain(self.dbconnection_1)
        self.showTableData(self.dbconnection_1)
        

    def delete_item(self):
        content = "SELECT * FROM Users"
        res = self.dbconnection_1.execute(content)
        for row in enumerate(res):
            if row[0] == self.tableWidget.currentRow():
                data        =  row[1]
                fname       = data[0]
                lname       = data[1]
                age         = data[2]
                birthday    = data[3]
                self.dbconnection_1.execute("DELETE FROM Users Where firstName=? and lastName=? and age=? and dob=?", (fname, lname, age, birthday,))
                self.dbconnection_1.commit()
                self.delete_db_table(self.dbconnection_2, str([fname, lname, age, birthday]))
                self.tableWidget.removeRow(self.tableWidget.currentRow())

        
    def showTableData(self, connection):
        result = connection.cursor().execute("""SELECT * FROM Users""")
        for row_number, row_data in enumerate(result):
            self.tableWidget.insertRow(row_number)
            for column_number, column_data in enumerate(row_data):
                item = str(column_data);
                self.tableWidget.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(item))


    def open_user(self):
        content = "SELECT * FROM Users"
        res = self.dbconnection_1.execute(content)
        for row in enumerate(res):
            if row[0] == self.tableWidget.currentRow():
                data        =  row[1]
                fname       = data[0]
                lname       = data[1]
                age         = data[2]
                birthday    = data[3]
        table_name = [str(fname), str(lname), str(age), str(birthday)]
        user = cataract_browser(str(table_name))
        user.exec()


    def proceed_save(self, ):
        content = "SELECT * FROM Users"
        res = self.dbconnection_1.execute(content)
        for row in enumerate(res):
            if row[0] == self.tableWidget.currentRow():
                data        =  row[1]
                fname       = data[0]
                lname       = data[1]
                age         = data[2]
                birthday    = data[3]
        table_name = [str(fname), str(lname), str(age), str(birthday)]
        self.email = data[5]
        save = save_analyze(os.path.join(self.path, self.name), None, str(table_name), self.email)
        save.exec()


class cataract_browser(QDialog, Database):
    def __init__(self, table_name):
        super(cataract_browser, self).__init__()
        Database.__init__(self)
        loadUi("cataract_browser.ui", self)
        self.showTableData(self.dbconnection_2, table_name)
    
    
    def showTableData(self, connection, table_name):
        result = connection.cursor().execute("""SELECT * FROM "{0}" """.format(table_name))
        for row_number, row_data in enumerate(result):
            self.tableWidget.insertRow(row_number)
            for column_number, column_data in enumerate(row_data):
                item = str(column_data);
                if(column_number == 0):
                    item = self.getImageLabel(column_data)
                    self.tableWidget.setCellWidget(row_number,column_number,item)
                else: 
                    self.tableWidget.setItem(row_number,column_number,QtWidgets.QTableWidgetItem(item))
        self.tableWidget.verticalHeader().setDefaultSectionSize(80)


    def getImageLabel(self,image):
        imageLabel = QtWidgets.QLabel(self.tableWidget)
        imageLabel.setText("")
        imageLabel.setScaledContents(True)
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(image,'png')
        imageLabel.setPixmap(pixmap)
        return imageLabel



if __name__ == '__main__':
    App = QApplication(sys.argv)
    Window = Main()
    Window.setWindowTitle("Camera")
    Window.show()
    sys.exit(App.exec_())