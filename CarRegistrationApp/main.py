#!/usr/bin/python3

#######################################################################################
#                                                                                     #
#  App to register cars.                                                              #
#  Car info is sent over MQTT to the timing server.                                   #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLabel, QLineEdit, QVBoxLayout, QComboBox, QMessageBox, QDialog
import paho.mqtt.client as paho
from config import Config
import sys
import csv
from datetime import datetime
import json

class MQTTHandler:
    def create_mqtt_connection(self):
        def on_connect(client, userdata, flags, reason_code, properties):
            if reason_code == 0:
                print("MQTT Client Connected")
            else:
                print("MQTT Client NOT Connected, rc= " + str(reason_code))
            client.subscribe("/timing/carreg/confirm_insert") #This goes here to sub on reconnection
            client.subscribe("/timing/carreg/confirm_update") #This goes here to sub on reconnection
            client.subscribe("/timing/carreg/failed") #This goes here to sub on reconnection
        client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=self.client_id)
        client.username_pw_set(Config.MQTT.USERNAME, Config.MQTT.PASSWORD)
        client.on_connect = on_connect
        client.connect(host=Config.MQTT.BROKER, port=Config.MQTT.PORT)
        return client
        
    def subHandler(self, client, userdata, msg):
        print("Message Received")
        if((msg.topic == "/timing/carreg/failed")):
            decoded_message = json.loads(str(msg.payload.decode("utf-8")))
            if(decoded_message["success"] == False):
                print("Radio for Nick Hills!")
                popup = getNickPopUpWindow()
                popup.exec()
        if((msg.topic == "/timing/carreg/confirm_insert") or (msg.topic == "/timing/carreg/confirm_update")):
            decoded_message = json.loads(str(msg.payload.decode("utf-8")))
            if(decoded_message["success"] == False):
                print("Radio for Nick Hills!")
                popup = getNickPopUpWindow()
                popup.exec()  # Use exec() for modal behavior
            else:
                # Clear the form when there is a successful submission
                print("Successful Submit")
                popup = successPopUpWindow()
                popup.exec()  # Use exec() for modal behavior
                self.mainWindow.tagScanBox.setText("")
                self.mainWindow.carNumberBox.setText("")
                self.mainWindow.teamNameComboBox.clear()
                self.mainWindow.teamNameComboBox.addItems(self.mainWindow.teamNameList)
                self.carClass = ""
            print(decoded_message)

    def __init__(self, mainWindow):
        super().__init__()

        self.mainWindow=mainWindow
        self.client_id = Config.MQTT.CLIENTID
        self.client = self.create_mqtt_connection()
        self.client.on_message = self.subHandler
        self.client.loop_start()

class MainWindow(QMainWindow):  
    
    def __init__(self):
        super().__init__()
        # Comment out to not fail when testing
        self.mqttClient = MQTTHandler(mainWindow=self)
        self.teamNameList = [""]
        self.carNumberList= [""]
        self.classList    = [""]
        self.carClass     = ""
        self.getCSVData()
        self.setStyleSheet('font-size: ' + str(26)+'px')

        self.setWindowTitle("Car Registration App")

        #create input boxes
        self.tagScanLabel = QLabel("Tag Data")
        self.tagScanBox = QLineEdit()
        self.tagScanBox.setStyleSheet("QLineEdit { margin-bottom: 20px; }")

        self.carNumberLabel = QLabel("Car Number")
        self.carNumberBox = QLineEdit()
        self.carNumberBox.setStyleSheet("QLineEdit { margin-bottom: 20px; }")
        self.teamNameLabel = QLabel("Team Name")

        self.teamNameComboBox=QComboBox()
        self.teamNameComboBox.addItems(self.teamNameList)
        self.teamNameComboBox.setStyleSheet("QComboBox { margin-bottom: 20px; }")
        self.teamNameComboBox.currentIndexChanged.connect(self.schoolChanged)
        
        #create button
        self.submitButton = QPushButton(text="Submit", parent=self)
        self.submitButton.setStyleSheet("QPushButton { padding: 15px; margin-bottom: 10px; background-color: green; }")
        self.submitButton.clicked.connect(self.submitButtonClicked)
        
        self.clearButton = QPushButton(text="Clear", parent=self)
        self.clearButton.setStyleSheet("background-color: red")
        self.clearButton.clicked.connect(self.clearButtonClicked)

        #create layout
        self.layout = QVBoxLayout()
        #self.layout.setSpacing(20)
        self.layout.addWidget(self.tagScanLabel)
        self.layout.addWidget(self.tagScanBox)

        self.layout.addWidget(self.carNumberLabel)
        self.layout.addWidget(self.carNumberBox)
        self.layout.addWidget(self.teamNameLabel)
        self.layout.addWidget(self.teamNameComboBox)
        self.layout.addWidget(self.submitButton)
        self.layout.addWidget(self.clearButton)

        self.container = QWidget()
        self.container.setLayout(self.layout)

        #set the central widget of the window
        self.setCentralWidget(self.container)

    def submitButtonClicked(self):
        print("Submit Button Pressed")
        if(self.tagScanBox.text() == "" or self.carNumberBox.text() == ""):
            print("Blank Fields Found, not submitting")
            popup = blankFieldsPopUpWindow()
            popup.exec()
        else:
            print(self.tagScanBox.text())
            data = {
                "car_number"    :   self.carNumberBox.text(),
                "team_name"     :   self.teamNameComboBox.currentText(),
                "tag_number"    :   self.tagScanBox.text(),
                "class"         :   self.carClass
                "scan_time"     :   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            data_json = json.dumps(data, indent=4)
            self.mqttClient.client.publish("/timing/carreg/newcar", payload=data_json, qos=0)
    
    def clearButtonClicked(self):
        print("Clear Button Pressed")
        self.tagScanBox.setText("")
        self.carNumberBox.setText("")
        self.teamNameComboBox.clear()
        self.teamNameComboBox.addItems(self.teamNameList)
        self.carClass = ""

    def getCSVData(self):
        with open('PS_2024_Registration.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.teamNameList.append(row['team_name'])
                self.carNumberList.append(row['car_number'])
                self.classList.append(row['class'])
    
    def schoolChanged(self):
        self.carNumberBox.setText(self.carNumberList[self.teamNameComboBox.currentIndex()])
        self.carClass = self.classList[self.teamNameComboBox.currentIndex()]

class getNickPopUpWindow(QDialog):
    def __init__(self):
        super().__init__()

        # Set the title and size of the popup
        self.setWindowTitle("Team Submission FAILED")
        self.setGeometry(100, 100, 400, 400)
        self.setStyleSheet('font-size: ' + str(48)+'px')

        # Add a label to the popup
        layout = QVBoxLayout()
        label = QLabel("Something didn't work!\nRadio for Nick Hills!", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class blankFieldsPopUpWindow(QDialog):
    def __init__(self):
        super().__init__()

        # Set the title and size of the popup
        self.setWindowTitle("Blanks Found")
        self.setGeometry(100, 100, 400, 400)
        self.setStyleSheet('font-size: ' + str(48)+'px')

        # Add a label to the popup
        layout = QVBoxLayout()
        label = QLabel("Blank Rows found\nNo submission.", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class successPopUpWindow(QDialog):
    def __init__(self):
        super().__init__()

        # Set the title and size of the popup
        self.setWindowTitle("Success")
        self.setGeometry(300, 300, 200, 200)
        self.setStyleSheet('font-size: ' + str(48)+'px')

        # Add a label to the popup
        layout = QVBoxLayout()
        label = QLabel("Success!", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

app = QApplication(sys.argv)

window = MainWindow()
window.setMinimumWidth(800)
window.show()

app.exec()

