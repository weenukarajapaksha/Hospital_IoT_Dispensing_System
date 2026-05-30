#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <WiFi.h>
#include <esp_now.h>
#include <cstring>

#define WATER_POT 34
#define CHEM_POT 35

#define WATER_VALVE 19
#define CHEM_PUMP 23
#define MIX_VALVE 25
#define WARNING_LED 33
#define BUZZER 32

#define TRIG_PIN 5
#define ECHO_PIN 18

#define TANK_OK_LED 19
#define TANK_LOW_LED 23

enum MessageType : uint8_t {
  REFILL_REQUEST = 1,
  REFILL_COMPLETE = 2,
  REFILL_FAILED = 3
};

struct WirelessMessage {
  uint8_t type;
  char text[24];
};

const uint8_t kBroadcastAddress[] = {0xff, 0xff, 0xff, 0xff, 0xff, 0xff};
const char *kSupplyMacAddress = "24:0A:C4:00:01:10";

LiquidCrystal_I2C lcd(0x27, 16, 2);

bool supplyRole = false;
bool requestSent = false;
volatile bool refillRequested = false;
volatile bool wirelessMessageAvailable = false;
WirelessMessage latestWirelessMessage = {};

void initWireless();
void onWirelessDataReceived(const uint8_t *mac, const uint8_t *data, int len);
void sendWirelessMessage(MessageType type, const char *text);

void supplySetup();
void supplyLoop();
void handleRefillRequest(int waterLevel, int chemLevel);
void errorAlarm(const String &message);
void stopAll();

void tankSetup();
void tankLoop();
void processWirelessMessage(int tankLevel);
int getTankLevelPercent();
void showTankStatus(int tankLevel, const char *status);

void setup() {
  Serial.begin(115200);
  initWireless();
  supplyRole = WiFi.macAddress().equalsIgnoreCase(kSupplyMacAddress);

  if (supplyRole) {
    supplySetup();
  } else {
    tankSetup();
  }
}

void loop() {
  if (supplyRole) {
    supplyLoop();
  } else {
    tankLoop();
  }
}

void initWireless() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init failed");
    return;
  }

  esp_now_register_recv_cb(onWirelessDataReceived);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, kBroadcastAddress, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;

  if (!esp_now_is_peer_exist(kBroadcastAddress)) {
    esp_now_add_peer(&peerInfo);
  }
}

void onWirelessDataReceived(const uint8_t *mac, const uint8_t *data, int len) {
  (void)mac;

  if (len != sizeof(WirelessMessage)) {
    return;
  }

  WirelessMessage message = {};
  memcpy(&message, data, sizeof(message));

  if (supplyRole && message.type == REFILL_REQUEST) {
    refillRequested = true;
    return;
  }

  if (!supplyRole && (message.type == REFILL_COMPLETE || message.type == REFILL_FAILED)) {
    latestWirelessMessage = message;
    wirelessMessageAvailable = true;
  }
}

void sendWirelessMessage(MessageType type, const char *text) {
  WirelessMessage message = {};
  message.type = type;
  strncpy(message.text, text, sizeof(message.text) - 1);

  esp_err_t result = esp_now_send(kBroadcastAddress, reinterpret_cast<uint8_t *>(&message), sizeof(message));

  Serial.print("ESP-NOW send ");
  Serial.print(text);
  Serial.print(": ");
  Serial.println(result == ESP_OK ? "OK" : "FAILED");
}

void supplySetup() {
  pinMode(WATER_VALVE, OUTPUT);
  pinMode(CHEM_PUMP, OUTPUT);
  pinMode(MIX_VALVE, OUTPUT);
  pinMode(WARNING_LED, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  lcd.init();
  lcd.backlight();
  stopAll();

  lcd.setCursor(0, 0);
  lcd.print("Supply ESP32");
  lcd.setCursor(0, 1);
  lcd.print("WiFi Ready");

  Serial.println("Supply ESP32 Ready");
  Serial.print("Supply MAC: ");
  Serial.println(WiFi.macAddress());

  delay(2000);
  lcd.clear();
}

void supplyLoop() {
  int waterLevel = map(analogRead(WATER_POT), 0, 4095, 0, 100);
  int chemLevel = map(analogRead(CHEM_POT), 0, 4095, 0, 100);

  lcd.setCursor(0, 0);
  lcd.print("W:");
  lcd.print(waterLevel);
  lcd.print("% C:");
  lcd.print(chemLevel);
  lcd.print("%   ");

  lcd.setCursor(0, 1);
  lcd.print("WiFi Waiting   ");

  if (refillRequested) {
    refillRequested = false;
    Serial.println("Received: REFILL_REQUEST");
    handleRefillRequest(waterLevel, chemLevel);
  }

  delay(300);
}

void handleRefillRequest(int waterLevel, int chemLevel) {
  if (waterLevel < 20) {
    errorAlarm("WATER LOW");
    sendWirelessMessage(REFILL_FAILED, "WATER LOW");
    return;
  }

  if (chemLevel < 15) {
    errorAlarm("CHEM LOW");
    sendWirelessMessage(REFILL_FAILED, "CHEM LOW");
    return;
  }

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Refill Started");

  digitalWrite(WATER_VALVE, HIGH);
  digitalWrite(CHEM_PUMP, HIGH);
  digitalWrite(MIX_VALVE, HIGH);

  for (int i = 0; i <= 100; i += 10) {
    lcd.setCursor(0, 1);
    lcd.print("Mixing: ");
    lcd.print(i);
    lcd.print("%   ");
    delay(500);
  }

  stopAll();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Refill Complete");
  lcd.setCursor(0, 1);
  lcd.print("WiFi Sent");

  sendWirelessMessage(REFILL_COMPLETE, "REFILL_COMPLETE");
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

void tankSetup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(TANK_OK_LED, OUTPUT);
  pinMode(TANK_LOW_LED, OUTPUT);

  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("Tank ESP32");
  lcd.setCursor(0, 1);
  lcd.print("WiFi Ready");

  Serial.println("Tank ESP32 Ready");
  Serial.print("Tank MAC: ");
  Serial.println(WiFi.macAddress());

  delay(2000);
  lcd.clear();
}

void tankLoop() {
  int tankLevel = getTankLevelPercent();

  Serial.print("Dispensing Tank Level: ");
  Serial.print(tankLevel);
  Serial.println("%");

  if (tankLevel < 25 && !requestSent) {
    digitalWrite(TANK_LOW_LED, HIGH);
    digitalWrite(TANK_OK_LED, LOW);
    showTankStatus(tankLevel, "Request Sent");

    sendWirelessMessage(REFILL_REQUEST, "REFILL_REQUEST");
    requestSent = true;
  }

  if (tankLevel >= 25 && !requestSent) {
    digitalWrite(TANK_OK_LED, HIGH);
    digitalWrite(TANK_LOW_LED, LOW);
    showTankStatus(tankLevel, "Tank OK");
  }

  if (requestSent) {
    showTankStatus(tankLevel, "Waiting Fill");
  }

  if (wirelessMessageAvailable) {
    wirelessMessageAvailable = false;
    processWirelessMessage(tankLevel);
  }

  delay(1000);
}

void processWirelessMessage(int tankLevel) {
  Serial.print("Received: ");
  Serial.println(latestWirelessMessage.text);

  if (latestWirelessMessage.type == REFILL_COMPLETE) {
    digitalWrite(TANK_OK_LED, HIGH);
    digitalWrite(TANK_LOW_LED, LOW);
    showTankStatus(100, "Refill Done");
    requestSent = false;
  }

  if (latestWirelessMessage.type == REFILL_FAILED) {
    digitalWrite(TANK_LOW_LED, HIGH);
    digitalWrite(TANK_OK_LED, LOW);
    showTankStatus(tankLevel, latestWirelessMessage.text);
    requestSent = false;
  }
}

int getTankLevelPercent() {
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
