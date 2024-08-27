from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLabel, QLineEdit, QVBoxLayout, QComboBox, QMessageBox
import paho.mqtt.client as paho
from Common.config import Config
import sys
import csv
from datetime import datetime
import json

# def create_mqtt_connection():
# 	def on_connect(client, userdata, flags, reason_code, properties):
# 		if reason_code == 0:
# 			print("MQTT Client Connected")
# 		else:
# 			print("MQTT Client NOT Connected, rc= " + str(reason_code))
# 		client.subscribe("/timing/TLCtrl/newpattern") #This goes here to sub on reconnection
# 	client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=client_id)
# 	client.username_pw_set(Config.MQTTUSERNAME, Config.MQTTPASSWORD)
# 	client.on_connect = on_connect
# 	client.connect(Config.TrafficLightActuator.MQTTBROKER, Config.MQTTPORT)
# 	return client
class MQTTHandler():

    def sub_handler():
        print("test")

    def create_mqtt_connection(self):
        def on_connect(client, userdata, flags, reason_code, properties):
            if reason_code == 0:
                print("MQTT Client Connected")
            else:
                print("MQTT Client NOT Connected, rc= " + str(reason_code))
            client.subscribe("/timing/carreg/newcar") #This goes here to sub on reconnection
            client.subscribe("/timing/carreg/confirm") #This goes here to sub on reconnection
        client = paho.Client(paho.CallbackAPIVersion.VERSION2,client_id=self.client_id)
        client.username_pw_set(Config.MQTTUSERNAME, Config.MQTTPASSWORD)
        client.on_connect = on_connect
        client.connect(host=Config.CarRegistration.MQTTBROKER, port=Config.MQTTPORT)
        return client
        
    def subHandler(self, client, userdata, msg):
        print("Message Received")
        if(msg.topic == "/timing/carreg/confirm"):
            decoded_message = str(msg.payload.decode("utf-8"))
            if(decoded_message == str(0)):
                print("Get Nick Hills")
                # MainWindow.show_popup(self)
            print(decoded_message)

    def __init__(self, parent=None):
        super().__init__()

        self.getNick = False
    
        self.client_id = Config.CarRegistration.MQTTCLIENTID
        self.client = self.create_mqtt_connection()
        self.client.on_message = self.subHandler
        self.client.loop_start()


class MainWindow(QMainWindow):  
    
    def __init__(self):
        super().__init__()

        self.mqttClient = MQTTHandler(self)
        self.teamNameList = []
        self.carNumberList= []
        self.getCSVData()

        self.setWindowTitle("Car Registration App")

        #create input boxes
        self.tagScanLabel = QLabel("Tag Data")
        self.tagScanBox = QLineEdit()

        self.carNumberLabel = QLabel("Car Number")
        self.carNumberBox = QLineEdit()
        self.teamNameLabel = QLabel("Team Name")
        self.teamNameBox = QLineEdit()
        # self.tagNumberLabel = QLabel("Tag Number")
        # self.tagNumberBox = QLineEdit()
        # self.scanTimeLabel = QLabel("Scan Time")
        # self.scanTimeBox = QLineEdit()

        self.teamNameComboBox=QComboBox()
        self.teamNameComboBox.addItems(self.teamNameList)
        self.teamNameComboBox.currentIndexChanged.connect(self.schoolChanged)
        

        #create button
        self.button = QPushButton(text="Submit", parent=self)
        # button.setCheckable(True)
        self.button.clicked.connect(self.buttonClicked)

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
        self.layout.addWidget(self.button)

        self.container = QWidget()
        self.container.setLayout(self.layout)

        #set the central widget of the window
        self.setCentralWidget(self.container)

    def buttonClicked(self):
        print("Button Pressed")
        print(self.tagScanBox.text())
        data = {
            "car_number"    :   self.carNumberBox.text(),
            "team_name"     :   self.teamNameComboBox.currentText(),
            "tag_number"    :   self.tagScanBox.text(),
            "scan_time"     :   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        data_json = json.dumps(data, indent=4)
        self.mqttClient.client.publish("/timing/carreg/newcar", payload=data_json, qos=0)

    def getCSVData(self):
        with open('carList.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.teamNameList.append(row['TeamName'])
                self.carNumberList.append(row['CarNumber'])
    
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


getNick = False

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()

