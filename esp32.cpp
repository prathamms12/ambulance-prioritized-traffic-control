/*
 * ================================================================
 * Project    : Ambulance Prioritized Traffic Control System
 * File       : ESP32_GPS_Transmitter.ino
 *
 * Author     : Pratham M S
 * Year       : 2026
 * GitHub     : https://github.com/your-username
 *
 * Description:
 * This ESP32 program reads GPS coordinates from a Neo-6M GPS module
 * and transmits the ambulance location to Firebase Realtime Database
 * over Wi-Fi. When GPS data is unavailable, predefined fallback
 * locations are used for testing. A push button triggers location
 * transmission, and an onboard LED indicates the transmission status.
 *
 * Technologies:
 * - ESP32
 * - Arduino Framework
 * - TinyGPS++
 * - Firebase Realtime Database
 * - HTTPClient
 * - Wi-Fi
 *
 * © 2026 Pratham M S. All Rights Reserved.
 * ================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <TinyGPS++.h>

// Wi-Fi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Firebase endpoint (must end with .json)
const char* firebase_url = "YOUR_FIREBASE_URL";

// GPS & Serial
TinyGPSPlus gps;
HardwareSerial gpsSerial(1);  // UART1 for GPS
#define RXPin 16
#define TXPin 17
#define GPSBaud 9600

// Button & LED pins
const int buttonPin = 4;
const int ledPin = 2;

bool lastButtonState = HIGH;
bool toggleLocation = false;  // To toggle between location 1 and 2

// Default locations
const float fallbackLat1 = 12.313046;
const float fallbackLon1 = 76.614105;
const float fallbackLat2 = 12.313049;
const float fallbackLon2 = 76.614100;

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(GPSBaud, SERIAL_8N1, RXPin, TXPin);

  pinMode(buttonPin, INPUT_PULLUP);  // Active LOW
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  // Connect Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi Connected");
}

void loop() {
  // Update GPS data
  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  bool buttonState = digitalRead(buttonPin);

  // Detect button press (active LOW)
  if (buttonState == LOW && lastButtonState == HIGH) {
    delay(50); // debounce

    float lat, lon;
    if (gps.location.isValid()) {
      lat = gps.location.lat();
      lon = gps.location.lng();
      Serial.println("📡 Valid GPS signal.");
    } else {
      // Toggle between the two locations
      if (toggleLocation) {
        lat = fallbackLat2;
        lon = fallbackLon2;
        Serial.println("⚠️ GPS not available. Using fallback location 2.");
      } else {
        lat = fallbackLat1;
        lon = fallbackLon1;
        Serial.println("⚠️ GPS not available. Using fallback location 1.");
      }
      toggleLocation = !toggleLocation;  // Toggle location for next press
    }

    Serial.printf("Sending Latitude: %.6f, Longitude: %.6f\n", lat, lon);

    // Blink LED while sending
    digitalWrite(ledPin, HIGH);

    // Create JSON
    String json = "{\"lat\":";
    json += String(lat, 6);
    json += ",\"lon\":";
    json += String(lon, 6);
    json += ",\"id\":\"ambulance-01\"}";

    // Send to Firebase
    HTTPClient http;
    http.begin(firebase_url);
    http.addHeader("Content-Type", "application/json");
    int response = http.PUT(json);
    Serial.println("📤 Sent: " + json);
    Serial.println("🔁 Firebase Response Code: " + String(response));
    http.end();

    digitalWrite(ledPin, LOW);  // Turn off after sending
  }

  lastButtonState = buttonState;
}
