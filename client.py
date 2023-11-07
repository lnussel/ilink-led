#!/usr/bin/python3
# SPDX-License-Identifier: LGPL-2.1-or-later


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

BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE =      'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE =    'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'

# this is a generic uuid
CLIENT_DESCR_UUID =    '00002902-0000-1000-8000-00805f9b34fb'

# ilink specific ones
ILINK_SERVICE_UUID =   '0000a032-0000-1000-8000-00805f9b34fb'
ILINK_WRITE_CHR_UUID =     '0000a040-0000-1000-8000-00805f9b34fb'
ILINK_READ_CHR_UUID =      '0000a041-0000-1000-8000-00805f9b34fb'
ILINKC_CLIENT_CHR_UUID = '0000a042-0000-1000-8000-00805f9b34fb'

ilinkled = None

class iLinkLED(object):
# The objects that we interact with.
    client_descr = None
    write_chrc = None
    write_chrc_if = None
    read_chrc = None

    def _build_cmd(self, *b):
        count = len(b)-2
        chk = -count & 0xFF
        for i in b:
            chk = (chk - i) & 0xFF
        return bytes([0x55, 0xaa, count] + list(b) + [chk])

    def _send(self, *b):
        if not self.write_chrc_if:
            self.write_chrc_if = dbus.Interface(self.write_chrc, GATT_CHRC_IFACE)
        cmd = self._build_cmd(*b)
        logger.debug("send %s", cmd)
        self.write_chrc_if.WriteValue(cmd, {'type': 'request'},
                                      reply_handler=lambda: logger.info("reply"),
                                      error_handler=generic_error_cb)

    def set_color(self, name):
        rgb = webcolors.name_to_rgb(name)
        self._send(0x08, 0x02, *rgb)

    def set_white(self, name):
        named = ['cold', 'natural', 'sunlight', 'evening', 'candle']
        if name in named:
            self._send(0x08, 0x09, named.index(name)+1)
        else:
            logging.error("Unknown value, choose from %s", ', '.join(named))

    def set_brightness(self, value):
        if value[0] == 'x':
            val = int(value[1:], 16)
        else:
            val = int(0xFF*int(value)/100)&0xFF
        self._send(0x08, 0x08, val)

def generic_error_cb(error):
    global mainloop
    logger.error(('D-Bus call failed: ' + str(error)))
    mainloop.quit()

# check whether we can handle the device at hand
def process_device(objects, path, chrc_paths):
    #obj = bus.get_object('org.bluez', path)
    #device = dbus.Interface(obj, 'org.bluez.Device1')
    obj = objects[path]
    if obj[GATT_SERVICE_IFACE]['UUID'] != ILINK_SERVICE_UUID:
        return None

    devpath = obj[GATT_SERVICE_IFACE]['Device']
    logger.debug(devpath)
    name = objects[devpath]['org.bluez.Device1']['Name']

    logger.debug("found %s - %s", objects[devpath]['org.bluez.Device1']['Address'], name)
    if not objects[devpath]['org.bluez.Device1']['Connected']:
        logger.error("Device %s (%s) not connected", name, devpath)

    dev = iLinkLED()
    for chrc_path in chrc_paths:
        chrc_obj = objects[chrc_path]
        uuid = chrc_obj[GATT_CHRC_IFACE]['UUID']
        logger.debug("%s: %s", chrc_path, uuid)
        # XXX FIXME this doesnt workas it's a descriptor below a charactersistic we are looking for
        if uuid == CLIENT_DESCR_UUID:
            logger.debug("found client charactersistic at %s", chrc_path)
            dev.client_descr = chrc_path
        elif uuid == ILINK_WRITE_CHR_UUID:
            logger.debug("found write charactersistic at %s", chrc_path)
            dev.write_chrc = bus.get_object(BLUEZ_SERVICE_NAME, chrc_path)
        elif uuid == ILINK_READ_CHR_UUID:
            logger.debug("found read charactersistic at %s", chrc_path)
            dev.read_chrc = bus.get_object(BLUEZ_SERVICE_NAME, chrc_path)

    global ilinkled
    ilinkled = dev

    return devpath

def main(args):
    # Set up the main loop.
    DBusGMainLoop(set_as_default=True)
    global bus
    bus = dbus.SystemBus()
    global mainloop
    mainloop = GLib.MainLoop()

    om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'), DBUS_OM_IFACE)

    logger.info('Getting objects...')
    objects = om.GetManagedObjects()
    chrcs = []

    # so the discovery interface seems to be a bit stupid here. We get flat
    # list of all paths. Then we find all paths that have charactersistics
    # attached. Then we look for paths that have a gatt interface. From there
    # we can get to the actual device and check it's name.

    # List characteristics found
    for path, interfaces in list(objects.items()):
        if GATT_CHRC_IFACE not in list(interfaces.keys()):
            continue
        logger.info("Gatt interface in %s", path)
        chrcs.append(path)

    # List sevices found
    for path, interfaces in list(objects.items()):
        if GATT_SERVICE_IFACE not in list(interfaces.keys()):
            continue

        logger.info("Gatt service in %s", path)
        chrc_paths = [d for d in chrcs if d.startswith(path + "/")]

        devpath = process_device(objects, path, chrc_paths)
        if devpath:
            break

    if not ilinkled:
        logger.error('No ilink device found')
        # FIXME: start scan and try again until timeout
        return 1

    if args.color:
        ilinkled.set_color(args.color)

    if args.white:
        ilinkled.set_white(args.white)

    if args.brightness:
        ilinkled.set_brightness(args.brightness)

    GLib.timeout_add_seconds(1, lambda: mainloop.quit() )

    mainloop.run()

    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                        description='boilerplate python commmand line program')
    parser.add_argument("--dry", action="store_true", help="dry run")
    parser.add_argument("--debug", action="store_true", help="debug output")
    parser.add_argument("--verbose", action="store_true", help="verbose")
    parser.add_argument("--color", action="store", help="color name")
    parser.add_argument("--white", action="store", help="color name")
    parser.add_argument("--brightness", action="store", help="color name")

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
