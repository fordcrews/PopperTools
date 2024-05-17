#include <BleKeyboard.h>

BleKeyboard bleKeyboard("XIAO ESP32C3 Keyboard", "ESP32C3", 100);

const int buttonPins[] = {2, 3, 4, 5, 6, 7, 8, 9};
const char keyMap[] = {KEY_END, '7', '8', '9', '0', '-', '=', 'n'};

void setup() {
  Serial.begin(115200);
  bleKeyboard.begin();

  for (int i = 0; i < 8; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
  }
}

void loop() {
  if (bleKeyboard.isConnected()) {
    for (int i = 0; i < 8; i++) {
      if (digitalRead(buttonPins[i]) == LOW) {
        bleKeyboard.press(keyMap[i]);
        delay(100);
        bleKeyboard.release(keyMap[i]);
        delay(100);
      }
    }
  }
  delay(10);
}

