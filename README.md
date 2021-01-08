# linux-gadget-hid
Example using linux with a micro-usb as a HID gadget (keyboard)

You will need a device with a microusb host port (e.g. Odroid C1, C2, C4, N2), and recent-enough kernel (>3.19) with support for libcomposite and usb_f_hid. Check that your kernel has support for them (either built-in or as modules):

```
$ zcat /proc/config.gz | egrep -i "libcomposite|usb_f_hid"
CONFIG_USB_LIBCOMPOSITE=y
CONFIG_USB_F_HID=y
```

# Dependencies:
  - python3
  - https://github.com/aagallag/hid_gadget_test

# How-to:
* Edit `create-hid.py` and set `vendor` and `description` to the strings you want
* Create a keyboard as a HID device:
```
$ sudo ./create-hid.py keyboard
```
Leave this process running (e.g. in the background). You can check on the USB host that the device is recognized as a keyboard when plugging in the USB cable:
```
$ dmesg
...
[ 6377.913325] usb 3-3: new high-speed USB device number 3 using xhci_hcd
[ 6378.062977] usb 3-3: New USB device found, idVendor=16c0, idProduct=0488, bcdDevice= 1.00
[ 6378.062981] usb 3-3: New USB device strings: Mfr=1, Product=2, SerialNumber=3
[ 6378.062984] usb 3-3: Product: Odroid Keyboard HID
[ 6378.062986] usb 3-3: Manufacturer: Gadget
[ 6378.062988] usb 3-3: SerialNumber: fedcba9876543210
[ 6378.065886] input: Gadget Odroid Keyboard HID as /devices/pci0000:00/0000:00:14.0/usb3/3-3/3-3:1.0/0003:16C0:0488.0004/input/input33
[ 6378.129950] hid-generic 0003:16C0:0488.0004: input,hidraw3: USB HID v1.01 Keyboard [Gadget Odroid Keyboard HID] on usb-0000:00:14.0-3/input0
```
* Edit `alt-tab.py` and set the correct paths to `hid_gadget_test` binary and `hid` (should be `/dev/hidg0` if you're running only one instance)
* Edit `alt-tab.py` to send the key sequences you want. You can see `hid_gadget_test`'s syntax by running it:
```
./hid_gadget_test /dev/hidg0 keyboard
```
* Plugging and unplugging the USB cable does not stop the processes!

# Credits
* ashren0 - for the `create-hid.py` code which does the heavy lifting to set things up

# Troubleshooting
* make sure the kernel has the necessary modules
* make sure the microusb port is in OTG mode (not host) (Set the dr_mode to dr_mode = "peripheral"). You might need to tweak the DTB as described here: https://forum.odroid.com/viewtopic.php?f=139&t=36602
* you can see keystrokes with `evtest` on the USB host device