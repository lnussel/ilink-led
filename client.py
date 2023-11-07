#!/usr/bin/python3
# SPDX-License-Identifier: MIT


import argparse
import dbus
import logging
import sys
import webcolors

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

bus = None
mainloop = None
logger = None
discovery_timeout = None

# leds that are connected
connected_devices = []

BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE =      'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE =    'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'
GATT_DSCR_IFACE =    'org.bluez.GattDescriptor1'

# this is a generic uuid
CLIENT_DESCR_UUID =      '00002902-0000-1000-8000-00805f9b34fb'

# ilink specific ones
ILINK_SERVICE_UUID =     '0000a032-0000-1000-8000-00805f9b34fb'
ILINK_WRITE_CHR_UUID =   '0000a040-0000-1000-8000-00805f9b34fb'
ILINK_READ_CHR_UUID =    '0000a041-0000-1000-8000-00805f9b34fb'
# notifications come in via this one
ILINKC_CLIENT_CHR_UUID = '0000a042-0000-1000-8000-00805f9b34fb'

# dictionary of path -> ledobj
_leds = {}

class iLinkLED(object):
# The objects that we interact with.
    service = None
    client_chrc = None
    write_chrc = None
    read_chrc = None
    dev = None
    name = None
    address = None
    connected = False

    status = {}

    def __init__(cls, dev):
        cls.dev = dev
        #logger.debug("%s %s", dev.object_path, dev.dbus_interface)

    # this method is supposed to be called on all device paths. It will pick the
    # relvant ones.
    @staticmethod
    def handle(path, interface):
        logger.debug(path)
        p = path.split('/')
        if len(p) < 5 or not p[4].startswith('dev_'):
            return False

        # found a known device, check whether path is a charactersistic we want
        # to handle
        if p[4] in _leds:
            led = _leds[p[4]]
            if GATT_CHRC_IFACE in interface:
                uuid = interface[GATT_CHRC_IFACE]['UUID']
            elif GATT_DSCR_IFACE in interface:
                uuid = interface[GATT_DSCR_IFACE]['UUID']
            elif GATT_SERVICE_IFACE in interface:
                uuid = interface[GATT_SERVICE_IFACE]['UUID']
            else:
                return False

            #logger.debug("%s: %s", path, uuid)
            if uuid == ILINK_SERVICE_UUID:
                logger.debug("found service interface %s", path)
                led.service = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, path), GATT_SERVICE_IFACE)
            elif uuid == ILINKC_CLIENT_CHR_UUID:
                logger.debug("found client descriptor at %s", path)
                led.client_chrc = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, path), GATT_CHRC_IFACE)
            elif uuid == ILINK_WRITE_CHR_UUID:
                logger.debug("found write charactersistic at %s", path)
                led.write_chrc = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, path), GATT_CHRC_IFACE)
            elif uuid == ILINK_READ_CHR_UUID:
                logger.debug("found read charactersistic at %s", path)
                led.read_chrc = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, path), GATT_CHRC_IFACE)

            if led.ready():
                led.start()
        else:
            if not 'org.bluez.Device1' in interface or not 'Name' in interface['org.bluez.Device1']:
                return False

            name = interface['org.bluez.Device1']['Name']
            if name == 'iLink app':
                address = interface['org.bluez.Device1']['Address']
                logger.debug("Found device %s %s", name, address)

                dev = dbus.Interface(bus.get_object('org.bluez', path), 'org.bluez.Device1')
                led = iLinkLED(dev)
                led.name = name
                led.address = address

                _leds[p[4]] = led

                if interface['org.bluez.Device1']['Connected']:
                    connected_devices.append(led)
                    led.connected = True
                    if led.ready():
                        led.start()
                else:
                    logger.info("Connecting %s", name)

                    def connect_cb(l):
                        logger.info("Connected %s", l.name)
                        global discovery_timeout
                        if discovery_timeout:
                            GLib.source_remove(discovery_timeout)
                            global mainloop
                            mainloop.quit()

                        led.connected = True
                        if l.ready():
                            l.start()
                        connected_devices.append(l)

                    def connect_timeout_cb(l):
                        if not led.connected:
                            logger.error("Timeout connecting %s", l.name)

                    global mainloop
                    if mainloop.is_running():
                        dev.Connect(reply_handler=lambda: connect_cb(led), error_handler=generic_error_cb)
                    else:
                        if dev.Connect():
                            connect_cb(led)
                        else:
                            logger.error("Failed to connect %s", name)

                    return True

        return False

    def ready(self):
        return not (not self.connected or self.dev is None or self.service is None or self.client_chrc is None or self.write_chrc is None or self.read_chrc is None)

    def _build_cmd(self, *b):
        count = len(b)-2
        chk = -count & 0xFF
        for i in b:
            chk = (chk - i) & 0xFF
        return bytes([0x55, 0xaa, count] + list(b) + [chk])

    def _send(self, *b):
        cmd = self._build_cmd(*b)
        logger.debug("send %s", ''.join(["%02x"%b for b in cmd]))
        self.write_chrc.WriteValue(cmd, {'type': 'request'})
        val = self.read_chrc.ReadValue([])
        self.parse_status(val)

    def parse_status(self, value):
        logger.debug("status %s", ''.join(["%02x"%b for b in value]))

        if len(value) < 5 or value[0] != 0x55 or value[1] != 0xaa:
            return False

        if (value[2] == 0x0a and value[3] == 0x88 and value[4] == 0x15) \
                or (value[2] == 0x09 and value[3] == 0x88 and value[4] == 0x18):
            self.status['red'] = int(value[5])
            self.status['green'] = int(value[6])
            self.status['blue'] = int(value[7])
            self.status['cold'] = int(value[8])
            self.status['warm'] = int(value[9])
            self.status['bright'] = int(value[10])
            logger.info("Color #%02x%02x%02x", self.status['red'], self.status['green'], self.status['blue'])
            logger.info("Cold %02x", self.status['cold'])
            logger.info("Warm %02x", self.status['warm'])
            logger.info("Brightness %02x", self.status['bright'])
            return True

        if value[2] == 0x05 and value[3] == 0x84 and value[4] == 0x14:
            self.status['equalizer'] = [int(i) for i in value[5:10]]
            logger.info("Equalizer %s", self.status['equalizer'])
            return True

        if value[2] == 0x01 and value[3] == 0x84 and value[4] == 0x04:
            self.status['volume'] = int(value[5])
            logger.info("Volume %02x", self.status['volume'])
            return True

        logger.debug("unhandled status")
        return False

    def start(self):
        logger.debug("Enable notifications")
        def changed_cb(interface, changed, invalidated):
            if interface == 'org.bluez.GattCharacteristic1' and 'Value' in changed:
                logger.debug("Changed: %s", bytes(changed['Value']))
                self.parse_status(changed['Value'])

        dbus.Interface(bus.get_object('org.bluez', self.client_chrc.object_path), DBUS_PROP_IFACE).connect_to_signal("PropertiesChanged", changed_cb)
        self.client_chrc.StartNotify()

    def set_color(self, name):
        if name == 'random':
            import random
            rgb = (random.randrange(0,0xFF),random.randrange(0,0xFF),random.randrange(0,0xFF))
        else:
            rgb = webcolors.name_to_rgb(name)
        self._send(0x08, 0x02, *rgb)

    def set_white(self, value):
        named = ['cold', 'natural', 'sunlight', 'evening', 'candle']
        if value in named:
            self._send(0x08, 0x09, named.index(value)+1)
        else:
            if value[0] == 'x':
                val = int(value[1:], 16)
            else:
                val = int(0xFF*int(value)/100)&0xFF

            if val > 255:
                logging.error("Invalid value, choose from %s, hex < xff or integer < 100", ', '.join(named))
            else:
                self._send(0x08, 0x07, val)

    def set_scene(self, name):
        scenes = ['rainbow1', 'rainbow2', 'heartbeat', 'breathe_red', 'breathe_green',
                  'breathe_blue', 'alarm', 'strobe', 'color_change', 'green_mood',
                  'evening_sun', 'rhythm']

        if name in scenes:
            self._send(0x08, 0x06, scenes.index(name)+1)
        else:
            logging.error("Unknown value, choose from %s", ', '.join(scenes))

    def set_equalizer(self, name):
        profiles = ['natural', 'classic', 'pop', 'bass', 'jazz']
        if ',' in name:
            values = name.split(',')
            if len(values) == 5:
                for i in range(0, 5):
                    val = int(values[i])
                    if val > 100:
                        logger.error("Value must be < 100")
                    else:
                        self._send(0x04, 0x0c + i, val)
            else:
                logging.error("Must be exactly five values")
        elif name in profiles:
            self._send(0x04, 0x05, profiles.index(name))
        else:
            logging.error("Unknown value, choose from %s", ', '.join(named))

    def set_brightness(self, value):
        if value[0] == 'x':
            val = int(value[1:], 16)
        else:
            val = int(0xFF*int(value)/100)&0xFF
        self._send(0x08, 0x08, val)

    def set_volume(self, value):
        if value[0] == 'x':
            val = int(value[1:], 16)
        else:
            val = int(0xFF*int(value)/100)&0xFF
        if val > 100:
            logger.error("Value must be < 100")
        else:
            self._send(0x04, 0x03, val)

    def power(self, value):
        self._send(0x08, 0x05, 1 if value else 0)

    def update_status(self):
        # volume
        self._send(0x04, 0x04)
        # equalizer
        self._send(0x04, 0x14)
        # light
        self._send(0x08, 0x15, 0x06)
        if False:
            # unknown
            self._send(0x05, 0x01, 0x11, 0x09, 0x33)
            # unknown
            self._send(0x05, 0x04, 0x06)
            # unknown
            self._send(0x05, 0x08, 0x06)
            # unknown
            self._send(0x05, 0x0c, 0x06)
            # unknown
            self._send(0x05, 0x22, 0x06)
            # unknown
            self._send(0x05, 0x23, 0x06)

    def print_status(self):
        self.update_status()
        for k, v in self.status.items():
            print(k, v)

def generic_error_cb(error):
    global mainloop
    logger.error('D-Bus call failed: %s', str(error))
    mainloop.quit()

def interfaces_removed_cb(object_path, interfaces):
    logger.debug("interfaces removed %s", object_path)
    # XXX remove handled device if it's one of ours

def interfaces_added_cb(object_path, interfaces):
    logger.debug("interfaces added %s %s", object_path, type(interfaces))

    iLinkLED.handle(object_path, interfaces)

def disconnect_all():
    for l in connected_devices:
        dev = l.dev
        logger.debug("Disconnecting %s %s", l.name, l.address)
        dev.Disconnect()

# XXX: shouldn't there be some convenience function already?
def get_prop(path, ifacename, propname):
    obj = bus.get_object(BLUEZ_SERVICE_NAME, path)
    iface = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')
    return iface.Get(ifacename, propname)

def main(args):
    # Set up the main loop.
    DBusGMainLoop(set_as_default=True)
    global bus
    bus = dbus.SystemBus()
    global mainloop
    mainloop = GLib.MainLoop()

    om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'), DBUS_OM_IFACE)
    om.connect_to_signal('InterfacesRemoved', interfaces_removed_cb)
    om.connect_to_signal('InterfacesAdded', interfaces_added_cb)

    objects = om.GetManagedObjects()

    adapters = set()

    # List characteristics found
    for path, interfaces in list(objects.items()):
        if iLinkLED.handle(path, interfaces):
            continue

        if 'org.bluez.Adapter1' in interfaces:
            logger.debug("found adapter at %s", path)
            adapters.add(path)

    if len(_leds) == 0 and args.scan:
        logger.error('No device found, scanning ...')
        for a in adapters:
            logger.debug("Enable discovery on %s", a)
            #bus.call_async('org.bluez', a, 'org.bluez.Adapter1', 'StartDiscovery', '', [], None, None)
            obj = bus.get_object(BLUEZ_SERVICE_NAME, a)
            device = dbus.Interface(obj, 'org.bluez.Adapter1')
#            def check_discovery():
#                logger.info("enabled discovery")
#                iface = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')
#                logger.debug(iface.Get('org.bluez.Adapter1', 'Discovering'))
#            device.StartDiscovery(reply_handler=check_discovery, error_handler=generic_error_cb)
            device.StartDiscovery()

            logger.debug("Running mainloop")
            global discovery_timeout
            discovery_timeout = GLib.timeout_add_seconds(15, lambda: mainloop.quit() )
            logger.debug("timeout %s", discovery_timeout)
            mainloop.run()

    if len(_leds) == 0:
        logger.error("No device found")
        return 1

    for ilinkled in _leds.values():
        if not ilinkled.ready():
            logger.error("Device not ready")
            continue

        if args.equalizer:
            ilinkled.set_equalizer(args.equalizer)

        if args.volume:
            ilinkled.set_volume(args.volume)

        if args.scene:
            ilinkled.set_scene(args.scene)

        if args.color:
            ilinkled.set_color(args.color)

        if args.white:
            ilinkled.set_white(args.white)

        if args.brightness:
            ilinkled.set_brightness(args.brightness)

        if args.on:
            ilinkled.power(True)
        elif args.off:
            ilinkled.power(False)

        if args.status:
            ilinkled.print_status()

        # run mainloop to get debug output from notifications
        if logger.getEffectiveLevel() < logging.INFO:
            GLib.timeout_add_seconds(1, lambda: mainloop.quit() )
            mainloop.run()

    if not args.stay_connected:
        disconnect_all()

    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                        description='boilerplate python commmand line program')
    parser.add_argument("--dry", action="store_true", help="dry run")
    parser.add_argument("--debug", action="store_true", help="debug output")
    parser.add_argument("--verbose", action="store_true", help="verbose")
    parser.add_argument("--scene", action="store", help="scene name")
    parser.add_argument("--color", action="store", help="color name")
    parser.add_argument("--white", action="store", help="set white light mode")
    parser.add_argument("--brightness", action="store", help="set brightness")
    parser.add_argument("--stay-connected", action="store_true", help="don't disconnect devices on exit")
    parser.add_argument("--scan", action="store_true", help="trigger scan if no device found")
    parser.add_argument("--equalizer", action="store", help="set equalizer")
    parser.add_argument("--volume", action="store", help="set volume")
    parser.add_argument("--on", action="store_true", help="turn the light on")
    parser.add_argument("--off", action="store_true", help="turn light off")
    parser.add_argument("--status", action="store_true", help="read status")

    args = parser.parse_args()

    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = None

    logging.basicConfig(level=level)

    logger = logging.getLogger("led-client")

    sys.exit(main(args))

# vim: sw=4 et
