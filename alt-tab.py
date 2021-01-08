#!/usr/bin/python3

# injects key strokes in an infinite loop
# needs hid_gadget_test to do the dirty work
# https://github.com/aagallag/hid_gadget_test

import pexpect
import time

#path to the hid_gadget_test binary
hid_gadget_test='/root/hid_gadget_test/hid_gadget_test'
#path to the hid node where to inject the keystrokes
hid='/dev/hidg0'

# ./hid_gadget_test /dev/hidg0 keyboard
p = pexpect.spawn(hid_gadget_test, [hid, "keyboard"])
while True:
    time.sleep(120)
    #send ALT+TAB every 2 minutes
    #a great way to look busy at work :)
    p.sendline("--left-alt --tab")
    p.expect("")
    print(p.before)
