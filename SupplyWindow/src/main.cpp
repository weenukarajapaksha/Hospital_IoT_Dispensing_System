#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <Wire.h>

#define WATER_POT 34
#define CHEM_POT 35

#define WATER_VALVE 19
#define CHEM_PUMP 23
#define MIX_VALVE 25
#define WARNING_LED 33
#define BUZZER 32

const char *WIFI_SSID = "Wokwi-GUEST";
const char *WIFI_PASSWORD = "";

const char *MQTT_HOST = "d26cc7cca3784e2486968e90e57f2349.s1.eu.hivemq.cloud";
const uint16_t MQTT_PORT = 8883;
const char *MQTT_USERNAME = "weenuka";
const char *MQTT_PASSWORD = "Weenuka@2003";

const char *TOPIC_REFILL_REQUEST = "hospital/refill/request";
const char *TOPIC_REFILL_STATUS = "hospital/refill/status";

LiquidCrystal_I2C lcd(0x27, 16, 2);
WiFiClientSecure secureClient;
PubSubClient mqtt(secureClient);

volatile bool refillRequested = false;
volatile int requestedTankLevel = 0;

void connectWiFi();
void connectMqtt();
void mqttCallback(char *topic, byte *payload, unsigned int length);
void stopAll();
void errorAlarm(const String &message);
void handleRefillRequest(int waterLevel, int chemLevel, int tankLevel);

void setup() {
  Serial.begin(115200);

  pinMode(WATER_VALVE, OUTPUT);
  pinMode(CHEM_PUMP, OUTPUT);
  pinMode(MIX_VALVE, OUTPUT);
  pinMode(WARNING_LED, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  lcd.init();
  lcd.backlight();
  stopAll();

  connectWiFi();
  secureClient.setInsecure();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
  connectMqtt();

  lcd.setCursor(0, 0);
  lcd.print("Supply ESP32");
  lcd.setCursor(0, 1);
  lcd.print("MQTT Ready");
  delay(2000);
  lcd.clear();
}

void loop() {
  if (!mqtt.connected()) {
    connectMqtt();
  }
  mqtt.loop();

  int waterLevel = map(analogRead(WATER_POT), 0, 4095, 0, 100);
  int chemLevel = map(analogRead(CHEM_POT), 0, 4095, 0, 100);

  lcd.setCursor(0, 0);
  lcd.print("W:");
  lcd.print(waterLevel);
  lcd.print("% C:");
  lcd.print(chemLevel);
  lcd.print("%   ");

  lcd.setCursor(0, 1);
  lcd.print("MQTT Waiting   ");

  if (refillRequested) {
    refillRequested = false;
    handleRefillRequest(waterLevel, chemLevel, requestedTankLevel);
  }

  delay(300);
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("WiFi connected: ");
  Serial.println(WiFi.localIP());
}

void connectMqtt() {
  while (!mqtt.connected()) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("MQTT Connect...");

    String clientId = "hospital-supply-" + String((uint32_t)ESP.getEfuseMac(), HEX);
    if (mqtt.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD)) {
      mqtt.subscribe(TOPIC_REFILL_REQUEST);
      Serial.println("MQTT connected as supply");
      lcd.setCursor(0, 1);
      lcd.print("Connected       ");
    } else {
      Serial.print("MQTT failed, rc=");
      Serial.println(mqtt.state());
      lcd.setCursor(0, 1);
      lcd.print("Retry MQTT      ");
      delay(3000);
    }
  }
}

void mqttCallback(char *topic, byte *payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += static_cast<char>(payload[i]);
  }

  Serial.print("MQTT received ");
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(message);

  if (String(topic) == TOPIC_REFILL_REQUEST && message.startsWith("REFILL_REQUEST")) {
    int separatorIndex = message.indexOf(':');
    requestedTankLevel = separatorIndex >= 0 ? message.substring(separatorIndex + 1).toInt() : 0;
    requestedTankLevel = constrain(requestedTankLevel, 0, 100);
    refillRequested = true;
  }
}

void handleRefillRequest(int waterLevel, int chemLevel, int tankLevel) {
  int refillAmount = 100 - constrain(tankLevel, 0, 100);
  int waterNeeded = refillAmount;
  int chemNeeded = max(5, refillAmount / 5);

  Serial.print("Tank level: ");
  Serial.print(tankLevel);
  Serial.print("%, refill amount: ");
  Serial.print(refillAmount);
  Serial.println("%");

  if (waterLevel < waterNeeded) {
    errorAlarm("WATER LOW");
    mqtt.publish(TOPIC_REFILL_STATUS, "REFILL_FAILED:WATER LOW");
    return;
  }

  if (chemLevel < chemNeeded) {
    errorAlarm("CHEM LOW");
    mqtt.publish(TOPIC_REFILL_STATUS, "REFILL_FAILED:CHEM LOW");
    return;
  }

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Need:");
  lcd.print(refillAmount);
  lcd.print("%");

  digitalWrite(WATER_VALVE, HIGH);
  digitalWrite(CHEM_PUMP, HIGH);
  digitalWrite(MIX_VALVE, HIGH);
  mqtt.publish(TOPIC_REFILL_STATUS, "REFILL_STARTED");

  for (int i = 0; i <= 100; i += 10) {
    lcd.setCursor(0, 1);
    lcd.print("Supplying:");
    lcd.print(i);
    lcd.print("%   ");
    String progress = "REFILL_PROGRESS:" + String(i);
    mqtt.publish(TOPIC_REFILL_STATUS, progress.c_str());
    delay(500);
    mqtt.loop();
  }

  stopAll();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Refill Complete");
  lcd.setCursor(0, 1);
  lcd.print("MQTT Sent");

  mqtt.publish(TOPIC_REFILL_STATUS, "REFILL_COMPLETE");
  delay(2000);
  lcd.clear();
}

void errorAlarm(const String &message) {
  stopAll();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ERROR!");
  lcd.setCursor(0, 1);
  lcd.print(message);

  digitalWrite(WARNING_LED, HIGH);
  tone(BUZZER, 1000);
  delay(3000);
  noTone(BUZZER);
  digitalWrite(WARNING_LED, LOW);
  lcd.clear();
}

void stopAll() {
  digitalWrite(WATER_VALVE, LOW);
  digitalWrite(CHEM_PUMP, LOW);
  digitalWrite(MIX_VALVE, LOW);
}
