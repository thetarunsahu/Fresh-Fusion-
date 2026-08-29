#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ135_PIN 34

const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* API_URL = "http://192.168.1.10:8000/api/v1/sensors/readings"; // laptop LAN IP
DHT dht(DHTPIN, DHTTYPE);

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print('.'); }
  Serial.print("\nESP32 IP: "); Serial.println(WiFi.localIP());
}

void setup(){ Serial.begin(115200); dht.begin(); connectWiFi(); }

void loop(){
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  float t=dht.readTemperature(); float h=dht.readHumidity(); int raw=analogRead(MQ135_PIN);
  if(!isnan(t) && !isnan(h)){
    HTTPClient http; http.begin(API_URL); http.addHeader("Content-Type","application/json");
    // sample_id is intentionally omitted. FreshFusion assigns telemetry to the newest active fruit sample.
    String body = String("{\"device_id\":\"ESP32_01\",\"temperature\":")+String(t,2)+",\"humidity\":"+String(h,2)+",\"mq135_raw\":"+String(raw)+",\"rssi\":"+String(WiFi.RSSI())+",\"uptime_ms\":"+String(millis())+"}";
    int code=http.POST(body); String response=http.getString();
    Serial.printf("HTTP %d | %s | %s\n",code,body.c_str(),response.c_str()); http.end();
  }
  delay(3000);
}
