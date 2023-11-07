# Reverse engineering the BLE protocol

This is how I analyzed the protocol:

- connect the Android phone with the app for the device via USB
- turn on HCI logging in the Android developer settings
- turn on Bluetooth
- open the app the do some defined action
- turn off logging and bluetooth again
- fetch the log on the computer: `adb pull /sdcard/btsnoop_hci.log`
- open the log file in `wireshark`
- check which packets are relevant and define a filter accordingly. `Wireshark` helps help with that. You can just right click on values to turn that value into a
  filter expression. The filter I used to filter out read, write and notification packets was `((bluetooth.dst == e8:0b:ba:b0:70:6d || bluetooth.src == e8:0b:ba:b0:70:6d) && ((btatt.opcode == 0x12 ) || (btatt.opcode == 0x0b)) || (btatt.opcode == 0x1b))`
- export the filtered packets as json
- pipe the json file through `jq` to get a nicely formatted list of packets sent and received: `jq -r '.[]|[._source.layers.btatt."btatt.opcode", ._source.layers.btatt."btatt.handle", (._source.layers.btatt."btatt.value"//""|gsub(":";""))]|join(" ")'`
- use `gatttool -I` to send packets to the device
