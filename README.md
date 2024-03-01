# WAF

A python daemon to control devices like tv, amp, players, etc based on activities

## With Activity Fun -> waf

Do not use, this is heaviliy WIP
Code is probably not working (its close now).
I am in the phase of restructuring an older version (hardcodes configs) that I had used many years.

## Aktivities

- Watch TV
- Watch TV with surround speakers
- Listen music via DLNA
- Watch Youtube with Chromcast
- Play with WII
- Listen FM Radio (Onkyo)
- Listen Internet Radio (Onkyo)
- Turn off all devices
- You name it

## Features

- Can use several remote control devices (at same time)
  - Reads from a local lirc socket
  - Reads from a remote lirc socket
  - Reads from a irmp device
- Can send IR signals to the lirc and irmp devices list above
- No need for irsend or similar tools
- No harcoded commands, addresses etc
  - Devices are configured in a yaml file
    - This includes hostname, mac addr., python classname, ...
  - IR Commands for actions are configured in a yaml file
    - Names do not need to be from 'KEY_' namespace, they can be anything.
    - Even direct IR signals like 'IRMP 15000f04c300' can be used
- Status leds can be
  - A single led connected to a GPIO that blinks in various speeds
  - A single led connected to an IRMP device that blinks in various speeds
  - A NeoPixel RGB stripe (8 leds) connected to an IRMP device (with NeoPixel support)
    - Back and forth sweep in different colors
- Control devices with IR or via Network if the device supports that
- 

## Supported devices

- LG TV with Nestcast interface
- Onkio Surround amplifier
- NAS (wake it up)
- Panasonic Blueray player
- Vdr

The above devices can be configured in the yaml file.
For other devices a short python class must be created that handles the activities.
Let me know if you need help. Pull requests are welcome.

## Reqirements

- Python 3.10 (older not tested)
- User must be member of groups: syslog, dialout and plugdev
  - syslog is required to access the logfile (/var/log/waf.log)
  - dialout and plugdev to access devices
- Lirc, IRMP devices (you can choose)
- For NeoPixel support you need a RP2040 based IRMP with my firmware.
  https://github.com/FauthD/IRMP_STM32


## Implementation

- A thread per device.
- All received IR signals are merged in a fifo, then dispatched to the activity state.
- The yaml config file controls the details. See waf-example.yaml.
