# Hardware Specification

## Doll: Vintage Animatronic (e.g., 1980s-style)
The original doll used a cassette tape mechanism with animatronic eyes and mouth. The retrofit will remove the cassette drive and repurpose the existing servo/solenoid infrastructure where possible.

## Raspberry Pi Selection

### Primary Target: Raspberry Pi Zero 2 W
- **CPU**: Quad-core 64-bit ARM Cortex-A53 @ 1GHz
- **RAM**: 512MB LPDDR2
- **Storage**: MicroSD (32GB+ recommended, Class 10/UHS-I)
- **Wireless**: 2.4GHz 802.11 b/g/n Wi-Fi, Bluetooth 4.2
- **USB**: 1x micro USB OTG (for hub or direct device)
- **GPIO**: 40-pin header for servo control
- **Power**: 5V/2.5A via micro USB or GPIO header
- **Rationale**: Fits inside the doll cavity; wireless eliminates extra cabling; lowest cost for multi-doll scaling.

### Fallback: Raspberry Pi 3 A+
- **CPU**: Quad-core 64-bit ARM Cortex-A53 @ 1.4GHz
- **RAM**: 512MB LPDDR2
- **USB**: 1x USB 2.0
- **Use if**: Zero 2 W is unavailable or if additional USB port is needed without a hub.

### Development/High-End: Raspberry Pi 4 (2GB/4GB)
- Used for development, testing server components locally, or for a "showcase" doll with local TTS fallback.

## Audio Hardware

### Microphone
- **Recommended**: USB MEMS microphone array (e.g., ReSpeaker 2-Mic Pi HAT or mini USB mic)
- **Specs**: 48kHz, 16-bit, mono or stereo
- **Placement**: Inside the doll chest, behind fabric, oriented toward the "face" direction
- **Alternative**: Bluetooth microphone (if USB port is scarce on Zero)

### Speakers
- **Recommended**: 3W 4Ω mini amplifier + speaker (e.g., Adafruit MAX98357A I2S amp + 3" speaker)
- **Placement**: Original speaker cavity if size permits; otherwise small speaker in chest cavity
- **Connection**: I2S (GPIO 18/19/21) preferred to free USB port; USB audio dongle as fallback

## Video Hardware

### Camera
- **Recommended**: Raspberry Pi Camera Module 3 (wide angle) or USB webcam (Logitech C270/C310)
- **Specs**: 720p@30fps minimum; 1080p@30fps preferred
- **Placement**: Inside one eye or forehead area (requires cutting/fabricating a lens cover)
- **Field of View**: Wide angle (120°+) preferred to capture room and people
- **Privacy**: Physical shutter or LED indicator when camera is active

## Servo / Actuator Hardware

### Existing Mechanism Reuse
- The original doll had two servo channels: eyes and mouth.
- The original servos may be 3V–5V analog; test and replace if necessary.

### New Servo Channels (Expansion)
| Channel | Actuator | Purpose | Servo Spec |
|---------|----------|---------|------------|
| 0 | Mouth | Lip sync / talking | 9g micro servo, 5V |
| 1 | Eyes (left/right) | Eye movement / looking | 9g micro servo, 5V |
| 2 | Eyelids | Blink / expression | 9g micro servo, 5V |
| 3 | Head tilt | Nod / look up/down | 9g micro servo, 5V |
| 4 | Head pan | Turn left/right | 9g micro servo, 5V |
| 5 | Left arm | Wave / gesture | 9g micro servo, 5V |
| 6 | Right arm | Wave / gesture | 9g micro servo, 5V |
| 7 | Torso / walking | Future: walking mechanism | Continuous rotation or stepper |

### Servo Controller
- **Primary**: PCA9685 16-channel PWM driver (I2C, 0x40) — handles all servos, frees GPIO
- **Power**: Separate 5V/3A BEC for servos; do not power from Pi GPIO

## Power Supply

### Inside the Doll
- **Battery**: 3.7V 18650 Li-ion (2x in parallel, with protection) or LiPo pack
- **Boost Converter**: 5V/3A step-up to power Pi and servos
- **Charging**: TP4056-based USB-C charging module with protection
- **Runtime Target**: 2–4 hours active use

### Tethered / Development
- 5V/3A USB-C power supply direct to Pi

## Networking
- **Primary**: Wi-Fi (2.4GHz) to local network / server
- **Fallback**: USB Ethernet adapter (Pi Zero requires OTG adapter)
- **Discovery**: mDNS (Avahi) or pre-configured static IP / config file on SD card

## Physical Integration Notes

### Cavity Space
- The doll has a foam body with a plastic chest cavity.
- Pi Zero 2 W (65mm × 30mm) fits with minor foam removal.
- Camera module may require routing through the neck or eye socket.
- Speaker placement should use existing acoustic chambers if possible.

### Cooling
- Passive cooling only (heatsink on Pi CPU)
- Ensure fabric does not block ventilation holes

### Cable Management
- Use thin silicone wire (28–30 AWG) for all internal connections
- Hot glue or 3D-printed brackets to secure components
- Leave service loop for head removal (if needed for maintenance)

## Bill of Materials (Per Doll)
| Item | Est. Cost | Qty | Notes |
|------|-----------|-----|-------|
| Raspberry Pi Zero 2 W | $15 | 1 | Or 3 A+ |
| MicroSD 32GB | $8 | 1 | Class 10 |
| Pi Camera Module 3 Wide | $35 | 1 | Or USB webcam |
| USB MEMS Mic | $10 | 1 | Or ReSpeaker HAT |
| MAX98357A I2S Amp | $6 | 1 | + 3" speaker |
| PCA9685 Servo Driver | $5 | 1 | 16-ch I2C |
| 9g Micro Servos (SG90) | $3 | 6 | Bulk pack |
| 18650 Li-ion + holder | $12 | 2 | With protection |
| 5V/3A Boost + TP4056 | $8 | 1 | Charging module |
| Misc wire, connectors | $10 | 1 | Silicone wire, headers |
| **Total per doll** | **~$120** | | |
