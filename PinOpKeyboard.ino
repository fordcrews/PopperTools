/*

 *  * Sample keyborad for pinball cabinets using ESP32 acting as a Bluetooth keyboard
 * Licensed under MIT License
 * https://opensource.org/licenses/MIT
 */

// This program lets an ESP32 act as a keyboard connected via Bluetooth.
// When a button attached to the ESP32 is pressed, it will generate the key strokes for a message.

// Change the below values if desired
#define DEVICE_NAME "PinOpKeyboard"

#define US_KEYBOARD 1

#include <Arduino.h>
#include "BLEDevice.h"
#include "BLEHIDDevice.h"
#include "HIDTypes.h"
#include "HIDKeyboardTypes.h"

// Define the button pins
const int buttonPins[] = {0, 1, 2, 3, 4, 5, 14, 15};

// Define the keys corresponding to each pin
const char customKeymap[] = {'e', '7', '8', '9', '0', '-', '=', 'n'};

// Message (report) sent when a key is pressed or released
struct InputReport {
    uint8_t modifiers;      // bitmask: CTRL = 1, SHIFT = 2, ALT = 4
    uint8_t reserved;       // must be 0
    uint8_t pressedKeys[6]; // up to six concurrently pressed keys
};

BLECharacteristic* input;
InputReport NO_KEY_PRESSED = {0, 0, {0, 0, 0, 0, 0, 0}};

const uint8_t REPORT_MAP[] = {
    0x05, 0x01,  // Usage Page (Generic Desktop)
    0x09, 0x06,  // Usage (Keyboard)
    0xA1, 0x01,  // Collection (Application)
    0x85, 0x01,  // Report ID (1)
    0x05, 0x07,  // Usage Page (Key Codes)
    0x19, 0xE0,  // Usage Minimum (224)
    0x29, 0xE7,  // Usage Maximum (231)
    0x15, 0x00,  // Logical Minimum (0)
    0x25, 0x01,  // Logical Maximum (1)
    0x75, 0x01,  // Report Size (1)
    0x95, 0x08,  // Report Count (8)
    0x81, 0x02,  // Input (Data, Variable, Absolute)
    0x95, 0x01,  // Report Count (1)
    0x75, 0x08,  // Report Size (8)
    0x81, 0x01,  // Input (Constant)
    0x95, 0x05,  // Report Count (5)
    0x75, 0x01,  // Report Size (1)
    0x05, 0x08,  // Usage Page (LEDs)
    0x19, 0x01,  // Usage Minimum (1)
    0x29, 0x05,  // Usage Maximum (5)
    0x91, 0x02,  // Output (Data, Variable, Absolute)
    0x95, 0x01,  // Report Count (1)
    0x75, 0x03,  // Report Size (3)
    0x91, 0x01,  // Output (Constant)
    0x95, 0x06,  // Report Count (6)
    0x75, 0x08,  // Report Size (8)
    0x15, 0x00,  // Logical Minimum (0)
    0x25, 0x65,  // Logical Maximum (101)
    0x05, 0x07,  // Usage Page (Key Codes)
    0x19, 0x00,  // Usage Minimum (0)
    0x29, 0x65,  // Usage Maximum (101)
    0x81, 0x00,  // Input (Data, Array)
    0xC0         // End Collection
};

// Forward declarations
void bluetoothTask(void*);
void sendKey(uint8_t key);
bool debounceButton(int pin);

bool isBleConnected = false;

class MyServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* server) {
        isBleConnected = true;
    }

    void onDisconnect(BLEServer* server) {
        isBleConnected = false;
        BLEAdvertising* advertising = server->getAdvertising();
        advertising->start();
    }
};

void setup() {
    Serial.begin(115200);

    // Configure pins for buttons
    for (int i = 0; i < 8; i++) {
        pinMode(buttonPins[i], INPUT_PULLUP);
    }

    // Start Bluetooth task
    xTaskCreate(bluetoothTask, "bluetooth", 20000, NULL, 5, NULL);
}

void loop() {  
    if (isBleConnected) {
        for (int i = 0; i < 8; i++) {
            if (debounceButton(buttonPins[i])) {
                sendKey(customKeymap[i]);
                delay(100);  // Additional debounce delay
            }
        }
    }

    delay(10);
}

bool debounceButton(int pin) {
    if (digitalRead(pin) == LOW) {
        delay(50);  // Debounce delay
        if (digitalRead(pin) == LOW) {
            return true;
        }
    }
    return false;
}

void sendKey(uint8_t key) {
    // Translate character to key combination
    uint8_t val = (uint8_t)key;
    if (val > KEYMAP_SIZE)
        return; // Character not available on keyboard - skip
    KEYMAP map = keymap[val];

    // Create input report
    InputReport report = {
        .modifiers = map.modifier,
        .reserved = 0,
        .pressedKeys = {
            map.usage,
            0, 0, 0, 0, 0
        }
    };

    // Send the input report
    input->setValue((uint8_t*)&report, sizeof(report));
    input->notify();

    delay(5);

    // Release all keys between two characters; otherwise two identical
    // consecutive characters are treated as just one key press
    input->setValue((uint8_t*)&NO_KEY_PRESSED, sizeof(NO_KEY_PRESSED));
    input->notify();

    delay(5);
}

void bluetoothTask(void*) {
    BLEDevice::init(DEVICE_NAME);
    BLEServer* server = BLEDevice::createServer();
    server->setCallbacks(new MyServerCallbacks());

    BLEHIDDevice* hid = new BLEHIDDevice(server);
    input = hid->inputReport(1); // <-- input REPORTID from report map
    hid->manufacturer()->setValue("Maker Community");

    hid->pnp(0x02, 0xe502, 0xa111, 0x0210);
    hid->hidInfo(0x00, 0x02);

    BLESecurity* security = new BLESecurity();
    security->setAuthenticationMode(ESP_LE_AUTH_BOND);

    hid->reportMap((uint8_t*)REPORT_MAP, sizeof(REPORT_MAP));
    hid->startServices();

    hid->setBatteryLevel(100);

    BLEAdvertising* advertising = server->getAdvertising();
    advertising->setAppearance(HID_KEYBOARD);
    advertising->addServiceUUID(hid->hidService()->getUUID());
    advertising->addServiceUUID(hid->deviceInfo()->getUUID());
    advertising->addServiceUUID(hid->batteryService()->getUUID());
    advertising->start();

    Serial.println("BLE ready");
    delay(portMAX_DELAY);
}
