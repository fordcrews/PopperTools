#include <BleKeyboard.h>

BleKeyboard bleKeyboard("ESP32 Keyboard", "ESP32", 100);

const int buttonPins[] = {22, 21, 17, 16, 32, 25, 27, 26};
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
