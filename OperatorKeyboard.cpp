#include <BleKeyboard.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN         12
#define NUMPIXELS       11
#define POWER_LED_INDEX 0
#define BT_LED_INDEX    1

BleKeyboard bleKeyboard("ESP32 BLE Keyboard", "ESP32", 100);
Adafruit_NeoPixel pixels(NUMPIXELS, LED_PIN, NEO_GRB + NEO_KHZ800);

const int buttonPins[] = {0, 1, 2, 3, 4, 5, 14, 15};
const char keyMap[] = {KEY_END, '7', '8', '9', '0', '-', '=', 'n'};

void setup() {
  Serial.begin(115200);
  bleKeyboard.begin();

  for (int i = 0; i < 8; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
  }

  pixels.begin();
  pixels.clear();
  
  // Turn on power indicator LED
  pixels.setPixelColor(POWER_LED_INDEX, pixels.Color(150, 0, 0)); // Red color for power
  pixels.show();
}

void loop() {
  if (bleKeyboard.isConnected()) {
    // Turn on Bluetooth status LED
    pixels.setPixelColor(BT_LED_INDEX, pixels.Color(0, 0, 150)); // Blue color for Bluetooth
  } else {
    // Turn off Bluetooth status LED
    pixels.setPixelColor(BT_LED_INDEX, pixels.Color(0, 0, 0)); // Off
  }
  pixels.show();

  for (int i = 0; i < 8; i++) {
    if (digitalRead(buttonPins[i]) == LOW) {
      bleKeyboard.press(keyMap[i]);
      delay(100);
      bleKeyboard.release(keyMap[i]);
      delay(100);

      // Light up corresponding pixel for button press
      pixels.setPixelColor(i + 2, pixels.Color(0, 150, 0));  // Set pixel to green
      pixels.show();
      delay(100);
      pixels.setPixelColor(i + 2, pixels.Color(0, 0, 0));    // Turn off pixel
      pixels.show();
    }
  }

  delay(10);
}
