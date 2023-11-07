# Protocol

Via GATT the device receives write requests on characteristic
0000a040-0000-1000-8000-00805f9b34fb. Some command return status that can be
fetched by reading characterstic
0000a041-0000-1000-8000-00805f9b34fb. To enable notifications, the
value 0x0100 has to be written to handle characterstic
00002902-0000-1000-8000-00805f9b34fb


The following example enables notifications, sets some white light
and requests equalizer status

    # gatttool -I
    > connect e8:0b:ba:b0:70:6d

    [e8:0b:ba:b0:70:6d][LE]> primary
    attr handle: 0x0001, end grp handle: 0x0003 uuid: 00001800-0000-1000-8000-00805f9b34fb
    attr handle: 0x0004, end grp handle: 0x0010 uuid: 0000a032-0000-1000-8000-00805f9b34fb
    [e8:0b:ba:b0:70:6d][LE]> char-desc 0x0001 0x0003
    handle: 0x0001, uuid: 00002800-0000-1000-8000-00805f9b34fb
    handle: 0x0002, uuid: 00002803-0000-1000-8000-00805f9b34fb
    handle: 0x0003, uuid: 00002a00-0000-1000-8000-00805f9b34fb
    [e8:0b:ba:b0:70:6d][LE]> char-desc 0x0004 0x0010
    handle: 0x0004, uuid: 00002800-0000-1000-8000-00805f9b34fb
    handle: 0x0005, uuid: 00002803-0000-1000-8000-00805f9b34fb
    handle: 0x0006, uuid: 0000a042-0000-1000-8000-00805f9b34fb
    handle: 0x0007, uuid: 00002902-0000-1000-8000-00805f9b34fb
    handle: 0x0008, uuid: 00002803-0000-1000-8000-00805f9b34fb
    handle: 0x0009, uuid: 0000a040-0000-1000-8000-00805f9b34fb
    handle: 0x000a, uuid: 00002803-0000-1000-8000-00805f9b34fb
    handle: 0x000b, uuid: 0000a041-0000-1000-8000-00805f9b34fb
    handle: 0x000c, uuid: 00002803-0000-1000-8000-00805f9b34fb
    handle: 0x000d, uuid: 0000a043-0000-1000-8000-00805f9b34fb
    handle: 0x000e, uuid: 00002902-0000-1000-8000-00805f9b34fb
    handle: 0x000f, uuid: 00002803-0000-1000-8000-00805f9b34fb
    handle: 0x0010, uuid: 0000a044-0000-1000-8000-00805f9b34fb

    [e8:0b:ba:b0:70:6d][LE]> char-write-req 0x0007 0100

    [e8:0b:ba:b0:70:6d][LE]> char-write-req 0x0009 55aa01080905e9
    Characteristic value was written successfully
    Notification handle = 0x0006 value: 55 aa 09 88 18 00 00 00 00 ff a5 01 01 16 9b

    [e8:0b:ba:b0:70:6d][LE]> char-write-req 0x0009 55aa01041406e1
    Characteristic value was written successfully
    [e8:0b:ba:b0:70:6d][LE]> char-read-hnd 0x000b
    Characteristic value/descriptor: 55 aa 05 84 14 32 32 32 32 32 69

## Commands

### Command 01 0403 -- Set Volume

Argument: volume  0x00-0xff

    55aa0104030bed
    55aa01040315e3
    55aa0104031bdd
    55aa01040320d8

See status 8404


### Command 01 0404 -- Get Volume Status?

See status 8404

    0x12 0x0009 55aa01040406f1
    0x0b 0x000b 55aa0184040770

### Command 01 0405 -- Set Equalizer Profiles

Argument 0x00-0x05

    0x12 0x0009 55aa01040500f6 # Natural
    0x0b 0x000b 55aa058414 32 32 32 32 32 69
    0x12 0x0009 55aa01040502f4 # Pop
    0x0b 0x000b 55aa058414 36 29 21 32 36 7b
    0x12 0x0009 55aa01040501f5 # Classic
    0x0b 0x000b 55aa058414 32 42 29 32 42 52
    0x12 0x0009 55aa01040504f2 # Jazz
    0x0b 0x000b 55aa058414 32 42 42 3a 3e 35
    0x12 0x0009 55aa01040503f3 # Bass
    0x0b 0x000b 55aa058414 3e 42 32 32 3a 45

See status 8414 for return value

### Command 01 0414 -- Equalizer status

See status 8414 for return value

    0x12 0x0009 55aa01041406e1
    0x0b 0x000b 55aa058414323232323269

### Command 01 040c -- Set Equalizer 80

Argument value from 0x00 - 0x64

    0x12 0x0009 55aa01040c00ef
    0x0b 0x000b 55aa00840c70
    0x12 0x0009 55aa01040c648b
    0x0b 0x000b 55aa00840c70

### Command 01 040d -- Set Equalizer 200

    0x12 0x0009 55aa01040d01ed
    0x0b 0x000b 55aa00840d6f
    0x12 0x0009 55aa01040d638b
    0x0b 0x000b 55aa00840d6f

### Command 00 040e -- Set Equalizer 400

    0x12 0x0009 55aa01040e00ed
    0x0b 0x000b 55aa00840e6e
    0x12 0x0009 55aa01040e628b
    0x0b 0x000b 55aa00840e6e

### Command 01 040f -- Set Equalizer 2k

    0x12 0x0009 55aa01040f05e7
    0x0b 0x000b 55aa00840f6d
    0x12 0x0009 55aa01040f6488
    0x0b 0x000b 55aa00840f6d

### Command 01 0410 -- Set Equalizer 8k

    0x12 0x0009 55aa0104105695
    0x0b 0x000b 55aa0084106c
    0x12 0x0009 55aa0104105b90
    0x0b 0x000b 55aa0084106c

### Command 03 0501 -- ??

    0x12 0x0009 55aa030501110933aa
    0x0b 0x000b 55aa0085017a

### Command 01 0504 -- ??

    0x12 0x0009 55aa01050406f0
    0x0b 0x000b 55aa0a85040014140b01010000000038

### Command 01 0508 -- ??

    0x12 0x0009 55aa01050806ec
    0x0b 0x000b 55aa0a85080014140b01010000000034

### Command 01 050c -- ??

    0x12 0x0009 55aa01050c06e8
    0x0b 0x000b 55aa0a850c0014140b01010000000030

### Command 01 0522 -- ??

    0x12 0x0009 55aa01052206d2
    0x0b 0x000b 55aa088522000000000000000051

### Command 01 0523 -- ??

    0x12 0x0009 55aa01052306d1
    0x0b 0x000b 55aa088523000000000000000050

### Command 01 0801 -- Set Brightness (color mode?)

Argument brightness 00-ff

    55aa01080105f1
    55aa0108012fc7
    55aa0108016096
    55aa0108019165
    55aa010801ca2c

### Command 03 0802 -- Set color

Argument RR GG BB

    55aa030802ff0000f4 # Red
    55aa030802ffff00f5 # Yellow
    55aa03080200ff00f4 # Green
    55aa03080200fffff5 # Cyan
    55aa0308020000fff4 # Blue
    55aa030802ff00fff5 # Pink

### Command 01 0805 -- Power, no notification

Argument 01 or 00 for ON/OFF

    55aa01080500f2  # OFF
    55aa01080501f1  # ON

### Command 01 0806 -- Scenes

    55aa01080601f0 # Rainbow 1
    55aa01080602ef # Rainbow 2
    55aa01080603ee # Heartbeat
    55aa01080604ed # Breathe red
    55aa01080605ec # Breathe green
    55aa01080606eb # Breathe blue
    55aa01080607ea # Alarm
    55aa01080608e9 # Strobe
    55aa01080609e8 # Color change
    55aa0108060ae7 # Green mood
    55aa0108060be6 # Evening sun
    55aa0108060ce5 # Rhythm

### Command 01 0808 -- brightness (used by app for white light)

    55aa01080801ee # low
    55aa01080811de
    55aa01080825ca
    55aa01080826c9
    55aa01080844ab
    55aa0108085a95
    55aa0108086887
    55aa010808747b
    55aa010808816e
    55aa010808915e
    55aa010808a44b
    55aa010808a54a
    55aa010808b23d
    55aa010808c728
    55aa010808d01f
    55aa010808d619
    55aa010808f8f7 # high

### Command 01 0809 -- White light temperature

Triggers notification

    55aa01080901ed # cold
    55aa01080902ec # natural
    55aa01080903eb # sunlight
    55aa01080904ea # evening sun
    55aa01080905e9 # candle

### Command 01 0815 -- ??

    0x12 0x0009 55aa01081506dc
    0x0b 0x000b 55aa0a881500000037c8100101167fb3

## Status return values

### Status 05 8404 -- Volume

| 00 | 01 | 02 | 03 | 04 | 05 | 06 |
|----|----|----|----|----|----|----|
| 55 | aa | 01 | 84 | 04 | VV | CS |

### Status 05 8414 -- Equalizer

| 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 0a |
|----|----|----|----|----|----|----|----|----|----|----|
| 55 | aa | 05 | 84 | 14 | V1 | V2 | V3 | V4 | V5 | CS |

V1 =  80 
V2 = 200 
V3 =  2k
V4 =  4K
V5 =  8k

Values are from 0x00 - 0x64

## Notification value

| 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 0a | 0b | 0c | 0d | 0e |
|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|
| 55 | aa | 09 | 88 | 18 | RR | GG | BB | T1 | T2 | BR | 01 | 01 | 16 | CS |

RR = Red value,
GG = Green value,
BB = Blue value,
T1 = White temperature,
T2 = White temperature,
BR = Brightness

## Checksum calculation

The checksum is calculated by substracting all byte values starting at pos 02 from 0.
