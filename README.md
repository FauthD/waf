# WAF Daemon

A python daemon to control devices like tv, amp, players, etc based on activities

## With Activity Fun -> waf

## Aktivities

- Watch TV
- Watch TV with surround speakers
- Listen music via DLNA
- Watch Youtube with Chromcast
- Play with a game device (e.G.: WII, ...)
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
- No hardcoded commands, addresses etc
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

## Supported devices

- LG TV with Netcast interface
- Onkio Surround amplifier
- NAS (wake it up)
- Panasonic Blueray player
- Vdr running on another machine
- Vdr running on local machine

The above devices can be configured in the yaml file.
For other devices a short python class must be created that handles the activities.
Let me know if you need help. Pull requests are welcome.

## Reqirements

- Python 3.10 (others not tested)
- Python modules see requirements.txt
- User must be member of groups: syslog, gpio, dialout and plugdev
  - syslog is required to access the logfile (/var/log/waf.log)
  - gpio is only required to access true GPIO bases status led (not needed for IRMP)
  - dialout and plugdev to access devices
- Lirc, IRMP devices (you can choose)
- For NeoPixel support you need a RP2040 based IRMP with my firmware.
  https://github.com/FauthD/IRMP_STM32
- SvdrPsend must be installed

## Implementation

- A thread per device.
- All received IR signals are merged in a fifo, then dispatched to the activity state.
- The yaml config file controls the details. See waf-example.yaml.

## Configuration examples

## Infraread receiving and transmitting

### LIRC on a remote machine

Assuming the name of the remote host is "regen".
Port must be the same as configured in the lirc configs.

```yaml
remotes:
  lirc_remote_rx:
    class: lirc
    host: regen
    port: 8766
```

### LIRC on a remote machine with separate instances for rx and tx

Assuming the name of the remote host is "regen".

```yaml
remotes:
  lirc_remote_rx:
    class: lirc
    tx: False
    rx: True
    host: regen
    port: 8766
  lirc_remote_tx:
    class: lirc
    tx: True
    rx: False
    host: regen
    port: 8765
```

### LIRC on local machine

```yaml
remotes:
  lirc_local:
    class: lirc
    socket: /run/lirc/lircd
```

### LIRC on local machine with separate instances for rx and tx

```yaml
remotes:
  lirc_local_rx:
    class: lirc
    tx: False
    socket: /run/lirc/lircd
  lirc_local_tx:
    class: lirc
    rx: False
    socket: /run/lirc/lircd-tx
```

### IRMP on local machine

```yaml
remotes:
  irmp:
    class: irmp
    device: /dev/irmp_stm32
```

### More than one receiver and transmitter

Data is received by all receivers.
Data is transmitted by all transmitters.

```yaml
remotes:
  irmp:
    class: irmp
    device: /dev/irmp_stm32
  lirc_local_rx:
    class: lirc
    tx: False
    socket: /run/lirc/lircd
  lirc_local_tx:
    class: lirc
    rx: False
    socket: /run/lirc/lircd-tx
  lirc_remote_rx:
    class: lirc
    tx: False
    rx: True
    host: regen
    port: 8766
  lirc_remote_tx:
    class: lirc
    tx: True
    rx: False
    host: regen
    port: 8765
```

## Dispatch IR Signals

All IR signals are merged into a single fifo and dispatched from there.
Use the ir-codes from either lirc conf files or irmp map files. Find the states in src/Helpers/states.py (dlna, movie, tv, ...).

```yaml
dispatch:
    WAF_DLNA: dlna
    WAF_MOVIE: movie
    WAF_TV: tv
    WAF_POWEROFF: alloff
    WAF_INETRADIO: iradio
    WAF_RADIO: radio
    WAF_CHROMECAST: chromecast
    WAF_BLUERAY: blueray
    WAF_GAME1: game1

    # Example for remote + key
    "OneForAll_URC7962_S1272 KEY_ZOOM": alloff

    # You can also use untranslated Ir-Codes
    'IRMP 15000f04c300': tv
    'IRMP 15000f04e300': movie
    'IRMP 15000f048300': dlna

    # Modifiers:
    WAF_TOGGLEMUTE: togglemute
    WAF_MUTE: mute
    WAF_UNMUTE: unmute
    KEY_MUTE: togglemute
    WAF_USESPEAKER: usespeaker
```

## Statusleds

### No LED

```yaml
status_led:
  # A dummy in case you do not need any LED:
  class: DummyLed
```

### A LED connected to a GPIO

```yaml
status_led:
  delay: 0.065
  class: GpiodLed
  chip: "/dev/gpiochip0" # BananaPro
  line: 226              # BananaPro Pin7
```

### A 8x Neopixel LED connected to a IRMP

```yaml
status_led:
  delay: 0.065

  # A NeoPixel strip with 8 leds on IRMP
  class: IrmpNeopixel
  device: /dev/irmp_stm32
  # RGB colors for NeoPixel sweep
  # Define as much as you have devices
  # The number is the number of busy devices
  colors:
    1: 30,20, 90
    2: 0,30,40
    3: 60,80,0
    4: 100,40,0
    5: 128,0,0
```

### A single LED connected to an IRMP

```yaml
status_led:
  # A LED connected to the status LED port of IRMP
  class: IrmpLed
  device: /dev/irmp_stm32
```

## Device config

### A LG TV from 2012

```yaml
devices:
  tv:
    mac: '11:22:33:44:55:66'
    name: "TV-42LM670S-ZA"
    class: 'LG_Netcast'
    KEY: "123456"
    # allows to mute the TV if the AMP is turned on
    RECEIVE_MUTE: True
    # default volumes
    TV_VOLUME: 14
    TV_CROMECAST: 14
    GAME1_VOLUME: 7

    # IR signals used to control the TV
    IR:
      POWER_ON: LG_TV LG_POWERON
      POWER_OFF: LG_TV LG_POWEROFF
      HDMI: LG_TV LG_HDMI
      HDMI1: LG_TV LG_HDMI1
      HDMI2: LG_TV LG_HDMI2
      HDMI3: LG_TV LG_HDMI3
      HDMI4: LG_TV LG_HDMI4
      GAME1: LG_TV LG_COMPONENT1

    # Assign the inputs
    INPUTS:
      BLUERAY: HDMI1
      CROMECAST: HDMI3
      VDR: HDMI4
      GAME1: GAME1
```

## A surround amplifier from Onkyo

```yaml
devices:
  amp:
    mac: '11:22:33:44:55:66'
    name: "TX-NR509"
    class: 'Onkyo'
    PORT: 60128
    # mute the TV
    SEND_MUTE: True
    # default volumes per connected source
    TV_VOLUME: 45
    BR_VOLUME: 28
    DLNA_VOLUME: 21
    FMRADIO_VOLUME: 28
    IRADIO_VOLUME: 20
    GAME1_VOLUME: 27
    CROMECAST_VOLUME: 28

    # IR signals used to control the Amp
    IR:
      POWER_ON: Onkyo_TX-NR509 ONKYO_POWERON
      POWER_OFF: Onkyo_TX-NR509 ONKYO_POWEROFF
      NET: Onkyo_TX-NR509 ONKYO_NET
      TV_CD: Onkyo_TX-NR509 ONKYO_TV_CD
      BD_DVD: Onkyo_TX-NR509 ONKYO_BD_DVD
      MUTE: Onkyo_TX-NR509 ONKYO_MUTE

    # Assign the inputs
    INPUTS:
      movie: TV_CD
      blueray: BD_DVD
      dlna: NET
    # These optional commands get executed on turn on/off
    Commands:
      OnTurnOn: 
        - 'zone2.power=standby'
      OnTurnOff: 
        - 'zone2.power=standby'
```

### A VDR on another machine

```yaml
devices:
  vdr:
    mac: '11:22:33:44:55:66'
    name: 'vdr'
    class: 'Vdr'

    # IR signals used to control the Amp
    IR:
      POWER_ON: IRMP KEY_POWER2
      POWER_OFF: OneForAll_URC7980_V1272 DF_POWEROFF

    # These optional commands get executed on turn on/off
    Commands:
      OnTurnOn: 
        - 'plug softhddevice ATTA'
      OnTurnOff: 
        - ['HITK STOP', '0.5']
        - 'HITK power'
```

