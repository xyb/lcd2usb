#!/usr/bin/env python
# encoding: utf8

'''blink.py - blink simle face which defined with two custom smile symbol
'''

import time

from lcd2usb import LCD, SMILE_SYMBOL, LCD2USBNotFound


BLINK_SMILE = bytearray([0x00, 0x00, 0x0a, 0x00, 0x11, 0x0e, 0x00, 0x00])


def blink(lcd):
    lcd.hello()

    while True:
        time.sleep(1)
        lcd.define_char(0, BLINK_SMILE)
        time.sleep(0.3)
        lcd.define_char(0, SMILE_SYMBOL)


if __name__ == '__main__':
    try:
        lcd = LCD()
    except LCD2USBNotFound, exc:
        print exc
        import sys
        sys.exit(-1)
    lcd.info()
    print 'version:', '%s.%s' % lcd.version
    blink(lcd)
