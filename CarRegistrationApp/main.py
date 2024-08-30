#/bin/python3

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
            client.subscribe("/timing/carreg/confirm") #This goes here to sub on reconnection
        client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=self.client_id)
        client.username_pw_set(Config.MQTTUSERNAME, Config.MQTTPASSWORD)
        client.on_connect = on_connect
        client.connect(host=Config.CarRegistrationApp.MQTTBROKER, port=Config.MQTTPORT)
        return client
        
    def subHandler(self, client, userdata, msg):
        print("Message Received")
        if(msg.topic == "/timing/carreg/confirm"):
            decoded_message = str(msg.payload.decode("utf-8"))
            if(decoded_message == str(0)):
                print("Radio for Nick Hills!")
                # MainWindow.show_popup(self)
                # Create an instance of the popup window and show it
                popup = getNickPopUpWindow()
                popup.exec()  # Use exec() for modal behavior
            #else:
                # Clear the form when there is a successful submission
                # How do we call this with "self" when the client is the "self"?
            #    clearButtonClicked(self)
            print(decoded_message)

    def __init__(self, mainWindow):
        super().__init__()

        self.getNick = False
        self.mainWindow=mainWindow
        self.client_id = Config.CarRegistrationApp.MQTTCLIENTID
        self.client = self.create_mqtt_connection()
        self.client.on_message = self.subHandler
        self.client.loop_start()

class MainWindow(QMainWindow):  
    
    def __init__(self):
        super().__init__()
        # Commented out to not fail when testing
        #self.mqttClient = MQTTHandler(mainWindow=self)
        self.teamNameList = [""]
        self.carNumberList= [""]
        self.getCSVData()
        self.setStyleSheet('font-size: ' + str(26)+'px')

        self.setWindowTitle("Car Registration App")

        #create input boxes
        self.tagScanLabel = QLabel("Tag Data")
        self.tagScanBox = QLineEdit()

        self.carNumberLabel = QLabel("Car Number")
        self.carNumberBox = QLineEdit()
        self.teamNameLabel = QLabel("Team Name")
        #self.teamNameBox = QLineEdit()
        # self.tagNumberLabel = QLabel("Tag Number")
        # self.tagNumberBox = QLineEdit()
        # self.scanTimeLabel = QLabel("Scan Time")
        # self.scanTimeBox = QLineEdit()

        self.teamNameComboBox=QComboBox()
        self.teamNameComboBox.addItems(self.teamNameList)
        self.teamNameComboBox.currentIndexChanged.connect(self.schoolChanged)
        

        #create button
        self.submitButton = QPushButton(text="Submit", parent=self)
        self.submitButton.setStyleSheet('margin: 20px')
        self.submitButton.setStyleSheet('padding: 5px')
        self.submitButton.clicked.connect(self.submitButtonClicked)
        
        self.clearButton = QPushButton(text="Clear", parent=self)
        self.clearButton.setStyleSheet('margin: 20px')
        self.clearButton.setStyleSheet('padding: 5px')
        self.clearButton.clicked.connect(self.clearButtonClicked)

        #create layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tagScanLabel)
        self.layout.addWidget(self.tagScanBox)
        # self.layout.addWidget(QLabel("----------OR----------"))

        self.layout.addWidget(self.carNumberLabel)
        self.layout.addWidget(self.carNumberBox)
        self.layout.addWidget(self.teamNameLabel)
        self.layout.addWidget(self.teamNameComboBox)
        # self.layout.addWidget(self.tagNumberLabel)
        # self.layout.addWidget(self.tagNumberBox)
        # self.layout.addWidget(self.scanTimeLabel)
        # self.layout.addWidget(self.scanTimeBox)
        self.layout.addWidget(self.submitButton)
        self.layout.addWidget(self.clearButton)

        self.container = QWidget()
        self.container.setLayout(self.layout)

        #set the central widget of the window
        self.setCentralWidget(self.container)

    def submitButtonClicked(self):
        print("Submit Button Pressed")
        print(self.tagScanBox.text())
        data = {
            "car_number"    :   self.carNumberBox.text(),
            "team_name"     :   self.teamNameComboBox.currentText(),
            "tag_number"    :   self.tagScanBox.text(),
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

    def getCSVData(self):
        with open('PS_2024_Registration.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.teamNameList.append(row['team_name'])
                self.carNumberList.append(row['car_number'])
    
    def schoolChanged(self):
        self.carNumberBox.setText(self.carNumberList[self.teamNameComboBox.currentIndex()])

    @staticmethod
    def show_popup(self):
        # Create a QMessageBox object
        msg = QMessageBox()

        # Set the title and message
        msg.setWindowTitle("Popup Window")
        msg.setText("This is a popup message!")

        # Add buttons to the popup
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Show the popup window
        msg.exec()

class getNickPopUpWindow(QDialog):
    def __init__(self):
        super().__init__()

        # Set the title and size of the popup
        self.setWindowTitle("Popup Window")
        self.setGeometry(100, 100, 200, 100)

        # Add a label to the popup
        layout = QVBoxLayout()
        label = QLabel("Radio for Nick Hills!", self)
        layout.addWidget(label)
        self.setLayout(layout)

getNick = False

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()

