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

#define SET_R_PIN 35
#define SET_Y_PIN 36
#define SET_G_PIN 39

#include <PubSubClient.h>

AsyncWebServer server(80);

// Set according to your local network if you need static IP
IPAddress myIP(192, 168,   2, 201);
IPAddress myGW(192, 168,   2,   1);
IPAddress mySN(255, 255, 255,   0);
IPAddress myDNS( 8,   8,   8,   8);
WiFiClient ethClient;

// MQTT Settings
const char *mqttServer     = "192.168.2.200";               // Broker address
const char *mqttBrokerUser = "username";                   // Username to connect to your MQTT broker
const char *mqttBrokerPass = "password";                   // Password to connect to your MQTT broker
const char *ID             = "TLCtrl";                     // Name of our device, must be unique
const int mqttPort         = 1883;
String PUB_TOPIC_0         = "/timing/TLCtrl/newpattern";  // Topic to publish to
String SUB_TOPIC_0         = "/timing/slscan/newscan";
String SUB_TOPIC_1         = "/timing/webui/override";
String HEALTH_CHECK_TOPIC  = "/timing/TLCtrl/healthcheck";
String HomePageText = "TLC Firmware Running.\nIP Address: 192.168.2.201\nUpdate at 192.168.2.201/update";
SemaphoreHandle_t xSemaphore = NULL;     // to track incoming scans
SemaphoreHandle_t ADAM_conneciton_status_change = NULL;     // in case the LED control box disconnects
int PatternStateTracker;
bool state_changed;
bool ADAM_connection_change = false;
bool scan_ready = false;
unsigned long yellow_pressed_time_ms = 0;
unsigned long green_pressed_time_ms  = 0;
unsigned long yellow_green_expiry_interval_ms = 5000;
unsigned long green_red_expiry_interval_ms    = 5000;

unsigned long prev_health_check = 0;
unsigned long health_check_interval = 30000; //ms
unsigned long prev_button_check = 0;
unsigned long button_check_interval = 100; //ms
unsigned long button_blink_interval = 500; //ms

//Callback for an incoming MQTT message
void callback(char* topic, byte* payload, unsigned int length) {
  if(String(topic) == SUB_TOPIC_0 || String(topic) == SUB_TOPIC_1){
    xSemaphoreGive(xSemaphore);  // Release the semaphore
  }
  if(String(topic) == String("Advantech/00D0C9FD648D/Device_Status")){
    xSemaphoreGive(ADAM_conneciton_status_change);  // Release the semaphore
  }
}

PubSubClient  client(mqttServer, mqttPort, callback, ethClient);

// TLC stuff
struct LED{
  int control_state;
  int prev_control_state;
  bool blink_state;
  unsigned long blink_time;
  String topic;
  String payload;
};

struct TLCButton{
  bool pressed;
  bool state;
};

struct TL{
  LED red_act;
  LED yellow_act;
  LED green_act;
  LED red_next;
  LED yellow_next;
  LED green_next;

  TLCButton red_button;
  TLCButton yellow_button;
  TLCButton green_button;

  int currState = 0;
  int prevState = 0;
};

TL TLC;
void readButton(int pin_num, bool *state, bool *pressed) {
  // digitalRead = 1 <- Button not pressed
  // digitalRead = 0 <- Button is pressed
  int buttonState = digitalRead(pin_num);
  //If button is pressed and the state is "pressed"
  //if (pin_num == 39) {
  //    Serial.println(buttonState);
  //}
  if (buttonState == 0 && *state == 1) {
    *pressed = !*pressed;
  }
  *state = buttonState;
  *state = !*state;
}

void controlLED(String topic, int *ctrl_state, int *prev_ctrl_state, bool *blink_state, unsigned long *blink_time ) {
  if (*ctrl_state == 2) { // blink
    if (millis() - *blink_time >= button_blink_interval) {
      *blink_time = millis();
      if (*blink_state) { //on
        client.publish(String(topic).c_str(), "{\"v\":true}");
        *blink_state = !*blink_state;
      }
      else { //off
        client.publish(String(topic).c_str(), "{\"v\":false}");
        *blink_state = !*blink_state;
      }
    }
  }
  else if (*ctrl_state == 1) { // on
    client.publish(String(topic).c_str(), "{\"v\":true}");
  }
  else { // off
    client.publish(String(topic).c_str(), "{\"v\":false}");
  }
  *prev_ctrl_state = *ctrl_state;
}

void controlTL(int *red_state, int *yellow_state, int *green_state) {
  client.publish(String("/timing/TLCtrl/newpattern").c_str(), String("{\"RedState\":" + String(*red_state) + ", \"YellowState\":" + String(*yellow_state) + ", \"GreenState\":" + String(*green_state) + "}").c_str());
}

void setup()
{
  pinMode(SET_R_PIN,INPUT);
  pinMode(SET_Y_PIN,INPUT);
  pinMode(SET_G_PIN,INPUT);
  
  Serial.begin(115200);
  while( !Serial ){ delay(10); }
  xSemaphore = xSemaphoreCreateBinary();  // Set the semaphore as binary
  ADAM_conneciton_status_change = xSemaphoreCreateBinary();  // Set the semaphore as binary

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

  // Create traffic light controller object and set it all to zeros.
  // init blink to 1 to make it light up sooner in blink state. 
  TLC.red_act     = {0, 0, 1, 0, "Advantech/00D0C9FD648D/ctl/do5",  ""};
  TLC.yellow_act  = {0, 0, 1, 0, "Advantech/00D0C9FD648D/ctl/do6",  ""};
  TLC.green_act   = {0, 0, 1, 0, "Advantech/00D0C9FD648D/ctl/do7",  ""};
  TLC.red_next    = {0, 0, 1, 0, "Advantech/00D0C9FD648D/ctl/do8",  ""};
  TLC.yellow_next = {0, 0, 1, 0, "Advantech/00D0C9FD648D/ctl/do9",  ""};
  TLC.green_next  = {0, 0, 1, 0, "Advantech/00D0C9FD648D/ctl/do10", ""};

  TLC.red_button = {0,0};
  TLC.yellow_button = {0,0};
  TLC.green_button = {0,0};

  // Initialize TLC to State 1 (SOLID RED)
  //TLC.red_act.control_state    = 1; 
  //controlLED(TLC.red_act.topic,     &TLC.red_act.control_state,     &TLC.red_act.prev_control_state,     &TLC.red_act.blink_state,     &TLC.red_act.blink_time     );
  //controlLED(TLC.yellow_act.topic,  &TLC.yellow_act.control_state,  &TLC.yellow_act.prev_control_state,  &TLC.yellow_act.blink_state,  &TLC.yellow_act.blink_time  );
  //controlLED(TLC.green_act.topic,   &TLC.green_act.control_state,   &TLC.green_act.prev_control_state,   &TLC.green_act.blink_state,   &TLC.green_act.blink_time   );
  //controlLED(TLC.red_next.topic,    &TLC.red_next.control_state,    &TLC.red_next.prev_control_state,    &TLC.red_next.blink_state,    &TLC.red_next.blink_time    );
  //controlLED(TLC.yellow_next.topic, &TLC.yellow_next.control_state, &TLC.yellow_next.prev_control_state, &TLC.yellow_next.blink_state, &TLC.yellow_next.blink_time );
  //controlLED(TLC.green_next.topic,  &TLC.green_next.control_state,  &TLC.green_next.prev_control_state,  &TLC.green_next.blink_state,  &TLC.green_next.blink_time  );
  // Write actual traffic light states
  //controlTL(&TLC.red_act.control_state, &TLC.yellow_act.control_state, &TLC.green_act.control_state);
  TLC.currState = 1;
  //TLC.prevState = 1;
}

void reconnect()
{
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection to " + String(mqttServer));
    // Attempt to connect
    if (client.connect(ID, mqttBrokerUser, mqttBrokerPass)) {
      Serial.println("...connected");
      client.subscribe(SUB_TOPIC_0.c_str());
      client.subscribe(SUB_TOPIC_1.c_str());
      client.subscribe(String("Advantech/00D0C9FD648D/Device_Status").c_str());
    }
    else {
      Serial.print("...failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
  client.publish(String("Advantech/00D0C9FD648D/ctl/do5").c_str(), "{\"v\":true}");
  client.publish(HEALTH_CHECK_TOPIC.c_str(), String("Im Alive with MAC " + ETH.macAddress()).c_str());
}

//Pattern State Tracker
// State 1:
//  TLA: RED (SOLID)
//  TLC: RED (SOLID)
// State 2: 
//  TLA; RED (SOLID)
//  TLC: YELLOW (FLASH)
// State 3:
//  TLA: YELLOW (SOLID)
//  TLC: YELLOW (SOLID), GREEN (FLASH)
// State 4:
//  TLA: GREEN (SOLID)
//  TLC: GREEN (SOLID)

void loop() 
{
  if (!client.connected()) { reconnect(); }
  if (millis() - prev_health_check > health_check_interval){
    if (!client.publish(HEALTH_CHECK_TOPIC.c_str(), "Im Still Alive")) { Serial.println("Message failed to send: " + String(HEALTH_CHECK_TOPIC)); }
    prev_health_check = millis();
  }

  if (millis() - prev_button_check > button_check_interval){

    //read button states
    readButton(SET_R_PIN, &TLC.red_button.state,    &TLC.red_button.pressed    );
    readButton(SET_Y_PIN, &TLC.yellow_button.state, &TLC.yellow_button.pressed );
    readButton(SET_G_PIN, &TLC.green_button.state,  &TLC.green_button.pressed  );

    // check if a scan flew in
    if (xSemaphoreTake(xSemaphore, (1 * portTICK_PERIOD_MS))  == pdTRUE) {
      scan_ready = true;
    }
    if (xSemaphoreTake(ADAM_conneciton_status_change, (1 * portTICK_PERIOD_MS))  == pdTRUE) {
      ADAM_connection_change = true;
    }

    //write states
    if(TLC.currState == 1)
    {
      if(scan_ready)
      {
        TLC.currState = 2;
        TLC.red_act.control_state     = 1;
        TLC.yellow_act.control_state  = 0;
        TLC.green_act.control_state   = 0;
        TLC.red_next.control_state    = 0;
        TLC.yellow_next.control_state = 2;
        TLC.green_next.control_state  = 0;
        scan_ready = false;
      }
      else if(TLC.red_button.state == 1)
      {
        TLC.currState = 1;
        TLC.prevState = 0;
        TLC.red_act.control_state     = 1; 
        TLC.red_act.prev_control_state= 0;
        TLC.yellow_act.control_state  = 0;
        TLC.green_act.control_state   = 0;
        TLC.red_next.control_state    = 0;
        TLC.yellow_next.control_state = 0;
        TLC.green_next.control_state  = 0;
      }
      else
      {
        //in state
        TLC.red_act.control_state     = 1; 
        TLC.yellow_act.control_state  = 0;
        TLC.green_act.control_state   = 0;
        TLC.red_next.control_state    = 0;
        TLC.yellow_next.control_state = 0;
        TLC.green_next.control_state  = 0;
      }
    }
    else if (TLC.currState == 2)
    {
      if(TLC.red_button.state == 1)
      {
        TLC.currState = 1;
        TLC.red_act.control_state     = 1; 
        TLC.yellow_act.control_state  = 0;
        TLC.green_act.control_state   = 0;
        TLC.red_next.control_state    = 0;
        TLC.yellow_next.control_state = 0;
        TLC.green_next.control_state  = 0;
      }
      else if (TLC.yellow_button.state == 1)
      {
        TLC.currState = 3;
        TLC.red_act.control_state     = 0; 
        TLC.yellow_act.control_state  = 1;
        TLC.green_act.control_state   = 0;
        TLC.red_next.control_state    = 0;
        TLC.yellow_next.control_state = 0;
        TLC.green_next.control_state  = 0;
        yellow_pressed_time_ms = millis();
      }
      else
      {
        //In state
        TLC.red_act.control_state     = 1; 
        TLC.yellow_act.control_state  = 0;
        TLC.green_act.control_state   = 0;
        TLC.red_next.control_state    = 0;
        TLC.yellow_next.control_state = 2;
        TLC.green_next.control_state  = 0;
      }
    }
    else if (TLC.currState == 3)
    {
      if (TLC.red_button.state == 1)
      {
        TLC.currState = 1;
        TLC.red_act.control_state     = 1; 
        TLC.yellow_act.control_state  = 0;
        TLC.green_act.control_state   = 0;
        TLC.red_next.control_state    = 0;
        TLC.yellow_next.control_state = 0;
        TLC.green_next.control_state  = 0;
      }
      else if (millis() - yellow_pressed_time_ms > yellow_green_expiry_interval_ms)
      {
        TLC.currState = 4;
        TLC.red_act.control_state     = 0; 
        TLC.yellow_act.control_state  = 0;
        TLC.green_act.control_state   = 1;
        TLC.red_next.control_state    = 0;
        TLC.yellow_next.control_state = 0;
        TLC.green_next.control_state  = 1;
        green_pressed_time_ms = millis();
      }
      else
      {
        //In State
        TLC.red_act.control_state     = 0; 
        TLC.yellow_act.control_state  = 1;
        TLC.green_act.control_state   = 0;
        TLC.red_next.control_state    = 0;
        TLC.yellow_next.control_state = 1;
        TLC.green_next.control_state  = 2;
      }
    }
    else if ( TLC.currState == 4)
    {
      if (TLC.red_button.state == 1 || millis() - green_pressed_time_ms > green_red_expiry_interval_ms)
      {
        TLC.currState = 1;
        TLC.red_act.control_state     = 1; 
        TLC.yellow_act.control_state  = 0;
        TLC.green_act.control_state   = 0;
        TLC.red_next.control_state    = 0;
        TLC.yellow_next.control_state = 0;
        TLC.green_next.control_state  = 0;
      }
      else
      {
        //In State
        TLC.red_act.control_state     = 0; 
        TLC.yellow_act.control_state  = 0;
        TLC.green_act.control_state   = 1;
        TLC.red_next.control_state    = 0;
        TLC.yellow_next.control_state = 0;
        TLC.green_next.control_state  = 1;
      }
    }
    if (ADAM_connection_change)
    {
      // Trick the system into going back to the default state. 
      TLC.currState = 1;
      TLC.prevState = 0;
      TLC.red_act.control_state     = 1;
      TLC.red_act.prev_control_state= 0;
      TLC.yellow_act.control_state  = 0;
      TLC.green_act.control_state   = 0;
      TLC.red_next.control_state    = 0;
      TLC.yellow_next.control_state = 0;
      TLC.green_next.control_state  = 0;
      ADAM_connection_change = false;
    }

    //write LED States
    if (TLC.currState != TLC.prevState ){
      // write traffic light states
      if(TLC.red_act.control_state != TLC.red_act.prev_control_state ) {
        controlLED(TLC.red_act.topic,     &TLC.red_act.control_state,     &TLC.red_act.prev_control_state,     &TLC.red_act.blink_state,     &TLC.red_act.blink_time     );
      }
      if(TLC.yellow_act.control_state != TLC.yellow_act.prev_control_state ) {
        controlLED(TLC.yellow_act.topic,  &TLC.yellow_act.control_state,  &TLC.yellow_act.prev_control_state,  &TLC.yellow_act.blink_state,  &TLC.yellow_act.blink_time  );
      }
      if(TLC.green_act.control_state != TLC.green_act.prev_control_state ) {
        controlLED(TLC.green_act.topic,   &TLC.green_act.control_state,   &TLC.green_act.prev_control_state,   &TLC.green_act.blink_state,   &TLC.green_act.blink_time   );
      }
      // Write actual traffic light states
      controlTL(&TLC.red_act.control_state, &TLC.yellow_act.control_state, &TLC.green_act.control_state);
      //write next-light states
      if(TLC.red_next.control_state != TLC.red_next.prev_control_state ) {
        controlLED(TLC.red_next.topic,     &TLC.red_next.control_state,     &TLC.red_next.prev_control_state,     &TLC.red_next.blink_state,     &TLC.red_next.blink_time     );
      }
      if(TLC.yellow_next.control_state != TLC.yellow_next.prev_control_state ) {
        controlLED(TLC.yellow_next.topic,  &TLC.yellow_next.control_state,  &TLC.yellow_next.prev_control_state,  &TLC.yellow_next.blink_state,  &TLC.yellow_next.blink_time  );
      }
      if(TLC.green_next.control_state != TLC.green_next.prev_control_state ) {
        controlLED(TLC.green_next.topic,   &TLC.green_next.control_state,   &TLC.green_next.prev_control_state,   &TLC.green_next.blink_state,   &TLC.green_next.blink_time   );
      }    
      TLC.prevState = TLC.currState;
      //Serial.print(int(TLC.currState));
      //Serial.println(int(TLC.prevState));
    }

    
    if ((TLC.red_next.control_state == 2) && (millis() - TLC.red_next.blink_time >= button_blink_interval)) {
      controlLED(TLC.red_next.topic,    &TLC.red_next.control_state,    &TLC.red_next.prev_control_state,    &TLC.red_next.blink_state,    &TLC.red_next.blink_time    );
      TLC.red_next.blink_time = millis();
    }
    if ((TLC.yellow_next.control_state == 2) && (millis() - TLC.yellow_next.blink_time >= button_blink_interval)) {
      controlLED(TLC.yellow_next.topic, &TLC.yellow_next.control_state, &TLC.yellow_next.prev_control_state, &TLC.yellow_next.blink_state, &TLC.yellow_next.blink_time );
      TLC.yellow_next.blink_time = millis();
    }
    if ((TLC.green_next.control_state == 2) && (millis() - TLC.green_next.blink_time >= button_blink_interval)) {
      controlLED(TLC.green_next.topic,  &TLC.green_next.control_state,  &TLC.green_next.prev_control_state,  &TLC.green_next.blink_state,  &TLC.green_next.blink_time  );
      TLC.green_next.blink_time = millis();
    }
  }
  delay(10);
  client.loop();
}


