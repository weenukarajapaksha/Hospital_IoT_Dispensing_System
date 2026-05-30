#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <Wire.h>

#define TRIG_PIN 5
#define ECHO_PIN 18

#define TANK_OK_LED 19
#define TANK_LOW_LED 23

const char *WIFI_SSID = "Wokwi-GUEST";
const char *WIFI_PASSWORD = "";

const char *MQTT_HOST = "d26cc7cca3784e2486968e90e57f2349.s1.eu.hivemq.cloud";
const uint16_t MQTT_PORT = 8883;
const char *MQTT_USERNAME = "weenuka";
const char *MQTT_PASSWORD = "Weenuka@2003";

const char *TOPIC_REFILL_REQUEST = "hospital/refill/request";
const char *TOPIC_REFILL_STATUS = "hospital/refill/status";

bool requestSent = false;
LiquidCrystal_I2C lcd(0x27, 16, 2);
WiFiClientSecure secureClient;
PubSubClient mqtt(secureClient);

String latestStatus = "";
// Wokwi ultrasonic distance stays fixed unless edited manually, so the refill
// progress messages are used to simulate the tank level rising during filling.
bool useSimulatedTankLevel = false;
int simulatedTankLevel = 0;
int refillStartLevel = 0;

void connectWiFi();
void connectMqtt();
void mqttCallback(char *topic, byte *payload, unsigned int length);
int getTankLevelPercent();
void showTankStatus(int tankLevel, const char *status);
void processRefillStatus(int tankLevel);
void setTankIndicators(int tankLevel);

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(TANK_OK_LED, OUTPUT);
  pinMode(TANK_LOW_LED, OUTPUT);

  lcd.init();
  lcd.backlight();

  connectWiFi();
  secureClient.setInsecure();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
  connectMqtt();

  lcd.setCursor(0, 0);
  lcd.print("Tank ESP32");
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

  int tankLevel = getTankLevelPercent();

  Serial.print("Dispensing Tank Level: ");
  Serial.print(tankLevel);
  Serial.println("%");

  if (tankLevel < 25 && !requestSent) {
    // Low level condition: warn locally and request a refill from supply ESP32.
    setTankIndicators(tankLevel);
    showTankStatus(tankLevel, "Request Sent");

    String requestMessage = "REFILL_REQUEST:" + String(tankLevel);
    mqtt.publish(TOPIC_REFILL_REQUEST, requestMessage.c_str());
    Serial.print("MQTT sent: ");
    Serial.println(requestMessage);

    requestSent = true;
    refillStartLevel = tankLevel;
    simulatedTankLevel = tankLevel;
    useSimulatedTankLevel = true;
  }

  if (tankLevel >= 25 && !requestSent) {
    setTankIndicators(tankLevel);
    showTankStatus(tankLevel, "Tank OK");
  }

  if (requestSent) {
    showTankStatus(tankLevel, "Waiting Fill");
  }

  if (latestStatus.length() > 0) {
    processRefillStatus(tankLevel);
  }

  delay(1000);
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

    String clientId = "hospital-tank-" + String((uint32_t)ESP.getEfuseMac(), HEX);
    if (mqtt.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD)) {
      mqtt.subscribe(TOPIC_REFILL_STATUS);
      Serial.println("MQTT connected as tank");
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

  if (String(topic) == TOPIC_REFILL_STATUS) {
    latestStatus = message;
  }
}

void processRefillStatus(int tankLevel) {
  String status = latestStatus;
  latestStatus = "";

  if (status == "REFILL_COMPLETE") {
    // Once supply reports completion, the dispensing tank is considered full.
    simulatedTankLevel = 100;
    useSimulatedTankLevel = true;
    setTankIndicators(simulatedTankLevel);
    showTankStatus(simulatedTankLevel, "Refill Done");
    requestSent = false;
    delay(2000);
    lcd.clear();
    return;
  }

  if (status.startsWith("REFILL_FAILED")) {
    setTankIndicators(tankLevel);
    showTankStatus(tankLevel, "Refill Failed");
    requestSent = false;
    useSimulatedTankLevel = false;
    return;
  }

  if (status == "REFILL_STARTED") {
    showTankStatus(tankLevel, "Refill Started");
    return;
  }

  if (status == "REFILL_STAGE:WATER_CHEM") {
    showTankStatus(tankLevel, "Water+Chem ON");
    return;
  }

  if (status == "REFILL_STAGE:MIXING") {
    showTankStatus(tankLevel, "Mixing");
    return;
  }

  if (status == "REFILL_STAGE:TRANSFER") {
    showTankStatus(tankLevel, "Filling Tank");
    return;
  }

  if (status.startsWith("REFILL_PROGRESS:")) {
    // Convert supply progress into a visible rising tank percentage.
    int progress = status.substring(status.indexOf(':') + 1).toInt();
    progress = constrain(progress, 0, 100);
    simulatedTankLevel = refillStartLevel + ((100 - refillStartLevel) * progress / 100);
    simulatedTankLevel = constrain(simulatedTankLevel, 0, 100);
    useSimulatedTankLevel = true;
    setTankIndicators(simulatedTankLevel);

    String displayText = "Filling " + String(progress) + "%";
    showTankStatus(simulatedTankLevel, displayText.c_str());
  }
}

int getTankLevelPercent() {
  if (useSimulatedTankLevel) {
    return simulatedTankLevel;
  }

  // Real/simulated ultrasonic measurement before a refill cycle begins.
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  float distance = duration * 0.034 / 2;

  float tankHeight = 100.0;
  float level = tankHeight - distance;

  if (level < 0) {
    level = 0;
  }

  if (level > tankHeight) {
    level = tankHeight;
  }

  return (level / tankHeight) * 100;
}

void showTankStatus(int tankLevel, const char *status) {
  lcd.setCursor(0, 0);
  lcd.print("Tank:");
  lcd.print(tankLevel);
  lcd.print("%        ");

  lcd.setCursor(0, 1);
  lcd.print(status);
  lcd.print("                ");
}

void setTankIndicators(int tankLevel) {
  if (tankLevel < 25) {
    digitalWrite(TANK_LOW_LED, HIGH);
    digitalWrite(TANK_OK_LED, LOW);
    return;
  }

  digitalWrite(TANK_LOW_LED, LOW);
  digitalWrite(TANK_OK_LED, HIGH);
}
