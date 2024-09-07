/****************************************************************************************************************************
  Based on the MQTT_And_OTA_Ethernet.ino Example
 *****************************************************************************************************************************/
/*
  To use OTA:   
    - Sketch > Export compiled binary
    - The file you will be uploading to do an OTA update is MQTT_And_OTA_Ethernet.ino.bin in build\esp32.esp32.esp32
    - Go to http://192.168.X.X/update with a browser (whatever your board IP is that you noted earlier.)
*/

#define DEBUG_ETHERNET_WEBSERVER_PORT       Serial
#define _ETHERNET_WEBSERVER_LOGLEVEL_       3            // Debug Level from 0 to 4
#define MAX_LINE_LENGTH (128)

#include <WebServer_WT32_ETH01.h>         // https://github.com/khoih-prog/WebServer_WT32_ETH01/
#include <AsyncTCP.h>                     // https://github.com/me-no-dev/AsyncTCP
//#include <ESPAsyncWebServer.h>            // https://github.com/me-no-dev/ESPAsyncWebServer
#include <ESPAsyncWebSrv.h>               // https://github.com/dvarrel/ESPAsyncWebSrv
//#include <AsyncElegantOTA.h>              // https://github.com/ayushsharma82/AsyncElegantOTA
# include <ElegantOTA.h>                  // https://github.com/ayushsharma82/ElegantOTA
//^^^^ Important, must set ASYNC mode, see the repo
//^^^^ Important, ElegantOTA tries to include "ESPAsyncWebServer.h", need to rename it in 
// Libraries also needed: https://github.com/knolleary/pubsubclient

#include <PubSubClient.h>
#include <ArduinoJson.h>

AsyncWebServer server(80);

// Set according to your local network if you need static IP
IPAddress myIP(192, 168,   2, 211);
IPAddress myGW(192, 168,   2,   1);
IPAddress mySN(255, 255, 255,   0);
IPAddress myDNS( 8,   8,   8,   8);
WiFiClient ethClient;

// MQTT Settings
const char *mqttServer     = "192.168.2.200";               // Broker address
const char *mqttBrokerUser = "username";                   // Username to connect to your MQTT broker
const char *mqttBrokerPass = "password";                   // Password to connect to your MQTT broker
const char *ID             = "flscan";                     // Name of our device, must be unique
const int mqttPort         = 1883;
String PUB_TOPIC_0         = "/timing/flscan/newscan";
String HEALTH_CHECK_TOPIC  = "/timing/flscan/healthcheck";
String HomePageText = "Finishline Firmware Running.\nIP Address: 192.168.2.211\nUpdate at 192.168.2.211/update";
String StoredScannedTagValue = "";
unsigned long StoredScannedTagTime = 0;
unsigned long StoredScannedTagTimeout = 10000;
unsigned long prev_health_check = 0;
unsigned long health_check_interval = 30000; //ms

TaskHandle_t rfid_scanner_reader_task;
TaskHandle_t rfid_scanner_write_task;

void TaskReadFromSerial(void *pvParameters);
void TaskWriteToSerial(void *pvParameters);

// Define Queue handle
QueueHandle_t QueueHandle;
const int QueueElementSize = 10;
typedef struct{
  char line[MAX_LINE_LENGTH];
  uint8_t line_length;
} message_t;

//Callback for an incoming MQTT message
void callback(char* topic, byte* payload, unsigned int length) 
{
  //Rogue
  Serial.print("Message arrived [" + String(topic) + "] ");  
  for (unsigned int i = 0; i < length; i++) { Serial.print((char)payload[i]); }
  Serial.println();
}

PubSubClient  client(mqttServer, mqttPort, callback, ethClient);

void setup()
{
  Serial.begin(115200);
  Serial2.setPins(5, 17);
  Serial2.begin(57600, SERIAL_8N1, 5,17);
  Serial2.setHwFlowCtrlMode(UART_HW_FLOWCTRL_DISABLE);
  while(!Serial || !Serial2) { delay(10); }
  // Create the queue which will have <QueueElementSize> number of elements, each of size `message_t` and pass the address to <QueueHandle>.
  QueueHandle = xQueueCreate(QueueElementSize, sizeof(message_t));
  // Check if the queue was successfully created
  if(QueueHandle == NULL){
    Serial.println("Queue could not be created. Halt.");
    while(1) delay(1000); // Halt at this point as is not possible to continue
  }

  WT32_ETH01_onEvent(); // To be called before ETH.begin()
  ETH.begin();
  ETH.config(myIP, myGW, mySN, myDNS);  //comment out for DHCP
  WT32_ETH01_waitForConnect();
  
  // Note - the default maximum packet size is 128 bytes. If the length
  // of clientId, u/n and p/w exceed this, increase the buffer size:
  // client.setBufferSize(255);

  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(200, "text/plain", HomePageText);
  });

  ElegantOTA.begin(&server);
  server.begin();
  Serial.println("HTTP server started with MAC: " + ETH.macAddress() + ", at IPv4: " + ETH.localIP().toString());

  // Following https://randomnerdtutorials.com/esp32-dual-core-arduino-ide/
  xTaskCreatePinnedToCore(
    TaskReadFromSerial2,          /* Function to implement the task */
    "TaskReadFromSerial2", /* Name of the task */
    2048,                      /* Stack size in words */
    NULL,                       /* Task input parameter */
    1,                          /* Priority of the task */
    &rfid_scanner_reader_task,  /* Task handle. */
    0);                         /* Core where the task should run */

  // Set up two tasks to run independently.
  xTaskCreatePinnedToCore(
    TaskWriteToSerial1
    ,  "TaskWriteToSerial1" // A name just for humans
    ,  2048        // The stack size can be checked by calling `uxHighWaterMark = uxTaskGetStackHighWaterMark(NULL);`
    ,  NULL        // No parameter is used
    ,  1  // Priority, with 3 (configMAX_PRIORITIES - 1) being the highest, and 0 being the lowest.
    ,  &rfid_scanner_write_task
    , 1);
}

void TaskReadFromSerial2(void *pvParameters){  // This is a task.
  message_t message;
  for (;;)
  {
    // Check if any data are waiting in the Serial buffer
    message.line_length = Serial2.available();
    if(message.line_length > 0){
      // Check if the queue exists AND if there is any free space in the queue
      if(QueueHandle != NULL && uxQueueSpacesAvailable(QueueHandle) > 0){
        int max_length = message.line_length < MAX_LINE_LENGTH ? message.line_length : MAX_LINE_LENGTH-1;
        for(int i = 0; i < max_length; i++){
          message.line[i] = Serial2.read();
        }
        message.line_length = max_length+1;
        message.line[message.line_length] = 0; // Add the terminating nul char

        // The line needs to be passed as pointer to void.
        // The last parameter states how many milliseconds should wait (keep trying to send) if is not possible to send right away.
        // When the wait parameter is 0 it will not wait and if the send is not possible the function will return errQUEUE_FULL
        int ret = xQueueSend(QueueHandle, (void*) &message, 0);
        if(ret == pdTRUE){
          // The message was successfully sent.
          Serial.println("Successfully sent scan data to queue");
        }else if(ret == errQUEUE_FULL){
          // Since we are checking uxQueueSpacesAvailable this should not occur, however if more than one task should
          // write into the same queue it can fill-up between the test and actual send attempt
          Serial.println("Unsuccessfully sent scan data to queue");
        } // Queue send check
      } // Queue sanity check
    }else{
      delay(100); // Allow other tasks to run when there is nothing to read
    } // Serial buffer check
  }
}

void TaskWriteToSerial1(void *pvParameters){  // This is a task.
  message_t message;
  message_t prevMessage;
  StaticJsonDocument<100> doc;
  char buffer[100];
  for (;;) // A Task shall never return or exit.
  {
    // One approach would be to poll the function (uxQueueMessagesWaiting(QueueHandle) and call delay if nothing is waiting.
    // The other approach is to use infinite time to wait defined by constant `portMAX_DELAY`:
    if(QueueHandle != NULL){ // Sanity check just to make sure the queue actually exists
      int ret = xQueueReceive(QueueHandle, &message, portMAX_DELAY);
      if(ret == pdPASS){
        // The message was successfully received - send it back to Serial port and "Echo: "
        Serial.printf("Echo line of size %d: \"%s\"\n\r", message.line_length, String(message.line));
        Serial.println("Successfully received scan data from queue");
        //for (int i = 0; i<(message.line_length-1); i++)
        //{
        //  Serial.println(message.line[i], HEX);//excludes NULL byte
        //}
        //Serial.println();
        String data = message.line;

        if(millis() - StoredScannedTagTime > StoredScannedTagTimeout) { StoredScannedTagValue = ""; }
        Serial.println("Length Check (17): " + String(data.length()));
        if(data != StoredScannedTagValue && data.length() == 17)
        {
          // The previously scanned tag data DOES NOT MATCH what just came in, sending out the MQTT message
          doc["tag_number"] = data;
          doc["tag_number_length"] = data.length();
          serializeJson(doc, buffer);
          const char *pubData = String(buffer).c_str();
          //const char *pubData = data.c_str();
          if (!client.publish(PUB_TOPIC_0.c_str(), pubData)) { Serial.println("Message failed to send: " + String(PUB_TOPIC_0)); }
          Serial.println("Message Send : " + String(PUB_TOPIC_0) + " => " + String(data));
          StoredScannedTagValue = data;
          StoredScannedTagTime = millis();
          buffer[0] = '\0';
        }
        else 
        { 
          Serial.println("Data and Stored are equal, or length of tag data wrong. NOT SENDING, TIMER RESET");
          StoredScannedTagTime = millis();
        }
      // The item is queued by copy, not by reference, so lets free the buffer after use.
      }
      else if(ret == pdFALSE){
        Serial.println("Unsuccessfully received scan data from queue");
      }
    } // Sanity check
  }
}

void reconnect()
{
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection to " + String(mqttServer));
    // Attempt to connect
    if (client.connect(ID, mqttBrokerUser, mqttBrokerPass)) {
      Serial.println("...connected");
    }
    else {
      Serial.print("...failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
  client.publish(HEALTH_CHECK_TOPIC.c_str(), String("Im Alive with MAC " + ETH.macAddress()).c_str());
}

void loop() 
{
  if (!client.connected()) { reconnect(); }
  if (millis() - prev_health_check > health_check_interval){
    if (!client.publish(HEALTH_CHECK_TOPIC.c_str(), "Im Still Alive")) { Serial.println("Message failed to send: " + String(HEALTH_CHECK_TOPIC)); }
    prev_health_check = millis();
  }
  delay(100);
  client.loop();
}


