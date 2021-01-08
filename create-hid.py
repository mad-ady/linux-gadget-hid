#!/usr/bin/python3

# Code by ashren0, taken from:
# https://forum.odroid.com/viewtopic.php?p=272788#p272788
# https://pastebin.com/V6W5e8Da
# needs a device with a microusb host and a kernel with libcomposite and usb_f_hid support

import sys
import os
import shutil
import pwd
import asyncio
import subprocess
import argparse
import atexit

vendor = 'Gadget'
description = "Odroid Keyboard"
 
class HIDReportDescriptorKeyboard(object):
    def __len__(self):
        return 8
 
    def __bytes__(self):
        return bytes([
            0x05, 0x01,  # Usage Page (Generic Desktop Ctrls)
            0x09, 0x06,  # Usage (Keyboard)
            0xA1, 0x01,  # Collection (Application)
            0x05, 0x07,  # Usage Page (Kbrd/Keypad)
            0x19, 0xE0,  # Usage Minimum (0xE0)
            0x29, 0xE7,  # Usage Maximum (0xE7)
            0x15, 0x00,  # Logical Minimum (0)
            0x25, 0x01,  # Logical Maximum (1)
            0x75, 0x01,  # Report Size (1)
            0x95, 0x08,  # Report Count (8)
            0x81, 0x02,  # Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
            0x95, 0x01,  # Report Count (1)
            0x75, 0x08,  # Report Size (8)
            0x81, 0x03,  # Input (Const,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
            0x95, 0x05,  # Report Count (5)
            0x75, 0x01,  # Report Size (1)
            0x05, 0x08,  # Usage Page (LEDs)
            0x19, 0x01,  # Usage Minimum (Num Lock)
            0x29, 0x05,  # Usage Maximum (Kana)
            0x91, 0x02,  # Output (Data,Var,Abs)
            0x95, 0x01,  # Report Count (1)
            0x75, 0x03,  # Report Size (3)
            0x91, 0x03,  # Output (Const,Var,Abs)
            0x95, 0x06,  # Report Count (6)
            0x75, 0x08,  # Report Size (8)
            0x15, 0x00,  # Logical Minimum (0)
            0x25, 0x65,  # Logical Maximum (101)
            0x05, 0x07,  # Usage Page (Kbrd/Keypad)
            0x19, 0x00,  # Usage Minimum (0x00)
            0x29, 0x65,  # Usage Maximum (0x65)
            0x81, 0x00,  # Input (Data,Array,Abs,No Wrap,Linear,Preferred State,No Null Position)
            0xC0,        # End Collection
        ])
 
 
class HIDReportDescriptorGamepad(object):
    def __len__(self):
        return 4
 
    def __bytes__(self):
        return bytes([
            0x05, 0x01,  # USAGE_PAGE (Generic Desktop)
            0x15, 0x00,  # LOGICAL_MINIMUM (0)
            0x09, 0x04,  # USAGE (Joystick)
            0xa1, 0x01,  # COLLECTION (Application)
            0x05, 0x02,  # USAGE_PAGE (Simulation Controls)
            0x09, 0xbb,  # USAGE (Throttle)
            0x15, 0x81,  # LOGICAL_MINIMUM (-127)
            0x25, 0x7f,  # LOGICAL_MAXIMUM (127)
            0x75, 0x08,  # REPORT_SIZE (8)
            0x95, 0x01,  # REPORT_COUNT (1)
            0x81, 0x02,  # INPUT (Data,Var,Abs)
            0x05, 0x01,  # USAGE_PAGE (Generic Desktop)
            0x09, 0x01,  # USAGE (Pointer)
            0xa1, 0x00,  # COLLECTION (Physical)
            0x09, 0x30,  # USAGE (X)
            0x09, 0x31,  # USAGE (Y)
            0x95, 0x02,  # REPORT_COUNT (2)
            0x81, 0x02,  # INPUT (Data,Var,Abs)
            0xc0,        # END_COLLECTION
            0x09, 0x39,  # USAGE (Hat switch)
            0x15, 0x00,  # LOGICAL_MINIMUM (0)
            0x25, 0x03,  # LOGICAL_MAXIMUM (3)
            0x35, 0x00,  # PHYSICAL_MINIMUM (0)
            0x46, 0x0e, 0x01,  # PHYSICAL_MAXIMUM (270)
            0x65, 0x14,  # UNIT (Eng Rot:Angular Pos)
            0x75, 0x04,  # REPORT_SIZE (4)
            0x95, 0x01,  # REPORT_COUNT (1)
            0x81, 0x02,  # INPUT (Data,Var,Abs)
            0x05, 0x09,  # USAGE_PAGE (Button)
            0x19, 0x01,  # USAGE_MINIMUM (Button 1)
            0x29, 0x04,  # USAGE_MAXIMUM (Button 4)
            0x15, 0x00,  # LOGICAL_MINIMUM (0)
            0x25, 0x01,  # LOGICAL_MAXIMUM (1)
            0x75, 0x01,  # REPORT_SIZE (1)
            0x95, 0x04,  # REPORT_COUNT (4)
            0x55, 0x00,  # UNIT_EXPONENT (0)
            0x65, 0x00,  # UNIT (None)
            0x81, 0x02,  # INPUT (Data,Var,Abs)
            0xc0         # END_COLLECTION
        ])
 
 
class HidDaemon(object):
    def __init__(self, vendor_id, product_id, manufacturer, description, serial_number, hid_report_class):
        self._descriptor = hid_report_class()
        self._hid_devname = 'odroidc2_hid'
        self._vendor = vendor_id
        self._product = product_id
        self._manufacturer = manufacturer
        self._desc = description
        self._serial = serial_number
        self._libcomposite_already_running = self.check_libcomposite()
        self._usb_f_hid_already_running = self.check_usb_f_hid()
        self._loop = asyncio.get_event_loop()
        self._devname = 'hidg0'
        self._devpath = '/dev/%s' % self._devname
 
    def _cleanup(self):
        udc_path = '/sys/kernel/config/usb_gadget/%s/UDC' % self._hid_devname
        if os.path.exists(udc_path):
            with open(udc_path, 'w') as fd:
                fd.truncate()
            try:
                shutil.rmtree('/sys/kernel/config/usb_gadget/%s' % self._hid_devname, ignore_errors=True)
            except:
                pass
        if not self._usb_f_hid_already_running and self.check_usb_f_hid():
            self.unload_usb_f_hid()
        if not self._libcomposite_already_running and self.check_libcomposite():
            self.unload_libcomposite()
 
    @staticmethod
    def check_libcomposite():
        #r = int(subprocess.check_output("lsmod | grep 'libcomposite' | wc -l", shell=True, close_fds=True).decode().strip())
        #return r != 0
        return True
 
    @staticmethod
    def load_libcomposite():
        if not HidDaemon.check_libcomposite():
            subprocess.check_call("modprobe libcomposite", shell=True, close_fds=True)
 
    @staticmethod
    def unload_libcomposite():
        if HidDaemon.check_libcomposite():
            subprocess.check_call("rmmod libcomposite", shell=True, close_fds=True)
 
    @staticmethod
    def check_usb_f_hid():
        r = int(subprocess.check_output("lsmod | grep 'usb_f_hid' | wc -l", shell=True, close_fds=True).decode().strip())
        return r != 0
 
    @staticmethod
    def load_usb_f_hid():
        if not HidDaemon.check_libcomposite():
            subprocess.check_call("modprobe usb_f_hid", shell=True, close_fds=True)
 
    @staticmethod
    def unload_usb_f_hid():
        if HidDaemon.check_libcomposite():
            subprocess.check_call("rmmod usb_f_hid", shell=True, close_fds=True)
 
    def _setup(self):
        f_dev_name = self._hid_devname
        os.makedirs('/sys/kernel/config/usb_gadget/%s/strings/0x409' % f_dev_name, exist_ok=True)
        os.makedirs('/sys/kernel/config/usb_gadget/%s/configs/c.1/strings/0x409' % f_dev_name, exist_ok=True)
        os.makedirs('/sys/kernel/config/usb_gadget/%s/functions/hid.usb0' % f_dev_name, exist_ok=True)
        with open('/sys/kernel/config/usb_gadget/%s/idVendor' % f_dev_name, 'w') as fd:
            fd.write('0x%04x' % self._vendor)
        with open('/sys/kernel/config/usb_gadget/%s/idProduct' % f_dev_name, 'w') as fd:
            fd.write('0x%04x' % self._product)
        with open('/sys/kernel/config/usb_gadget/%s/bcdDevice' % f_dev_name, 'w') as fd:
            fd.write('0x0100')
        with open('/sys/kernel/config/usb_gadget/%s/bcdUSB' % f_dev_name, 'w') as fd:
            fd.write('0x0200')
 
        with open('/sys/kernel/config/usb_gadget/%s/strings/0x409/serialnumber' % f_dev_name, 'w') as fd:
            fd.write(self._serial)
        with open('/sys/kernel/config/usb_gadget/%s/strings/0x409/manufacturer' % f_dev_name, 'w') as fd:
            fd.write(self._manufacturer)
        with open('/sys/kernel/config/usb_gadget/%s/strings/0x409/product' % f_dev_name, 'w') as fd:
            fd.write(self._desc)
 
        with open('/sys/kernel/config/usb_gadget/%s/configs/c.1/strings/0x409/configuration' % f_dev_name, 'w') as fd:
            fd.write('Config 1 : %s' % self._desc)
        with open('/sys/kernel/config/usb_gadget/%s/configs/c.1/MaxPower' % f_dev_name,'w') as fd:
            fd.write('250')
 
        with open('/sys/kernel/config/usb_gadget/%s/functions/hid.usb0/protocol' % f_dev_name, 'w') as fd:
            fd.write('1')
        with open('/sys/kernel/config/usb_gadget/%s/functions/hid.usb0/subclass' % f_dev_name, 'w') as fd:
            fd.write('1')
        with open('/sys/kernel/config/usb_gadget/%s/functions/hid.usb0/report_length' % f_dev_name, 'w') as fd:
            fd.write(str(len(self._descriptor)))
        with open('/sys/kernel/config/usb_gadget/%s/functions/hid.usb0/report_desc' % f_dev_name, 'wb') as fd:
            fd.write(bytes(self._descriptor))
 
        os.symlink(
            '/sys/kernel/config/usb_gadget/%s/functions/hid.usb0' % f_dev_name,
            '/sys/kernel/config/usb_gadget/%s/configs/c.1/hid.usb0' % f_dev_name,
            target_is_directory=True
        )
 
        with open('/sys/kernel/config/usb_gadget/%s/UDC' % f_dev_name, 'w') as fd: fd.write('\r\n'.join(os.listdir('/sys/class/udc')))
 
    def run(self):
        if not self._libcomposite_already_running:
            self.load_libcomposite()
        atexit.register(self._cleanup)
 
        # Setup HID gadget (keyboard)
        self._setup()
 
        # Use asyncio because we can then do thing on the side (web ui, polling attached devices using pyusb ...)
        try:
            self._loop.run_forever()
        except KeyboardInterrupt:
            pass
 
if __name__ == '__main__':
    user_root = pwd.getpwuid(0)
    user_curr = pwd.getpwuid(os.getuid())
    print('Running as <%s>' % user_curr.pw_name)
    if os.getuid() != 0:
        print('Attempting to run as <root>')
        sys.exit(os.system("/usr/bin/sudo /usr/bin/su root -c '%s %s'" % (sys.executable, ' '.join(sys.argv))))
    parser = argparse.ArgumentParser()
    parser.add_argument('hid_type', choices=['keyboard', 'gamepad'])
    args = parser.parse_args()
    if args.hid_type == 'keyboard':
        print('Emulating: Keyboard')
        # Generic keyboard
        hid = HidDaemon(0x16c0, 0x0488, vendor, description+' HID', 'fedcba9876543210', HIDReportDescriptorKeyboard)
        hid.run()
    elif args.hid_type == 'gamepad':
        print('Emulating: Gamepad')
        # Teensy FlightSim for the purpose of this example (and since it's intended for DIY, it fits our purpose)
        hid = HidDaemon(0x16c0, 0x0488, vendor, description+' HID', 'fedcba9876543210', HIDReportDescriptorGamepad)
        hid.run()
