#!/usr/bin/env python
# encoding: utf8

'''Python wrapper for LCD2USB
'''

import ctypes
import struct

import libusb1
import usb1


# vendor and product id
LCD2USB_VENDOR_ID = 0x0403
LCD2USB_PRODUCT_ID = 0xc630

# target is a bit map for CMD/DATA
LCD_CTRL_0 = 1 << 3
LCD_CTRL_1 = 1 << 4
LCD_BOTH = LCD_CTRL_0 | LCD_CTRL_1

LCD_ECHO = 0 << 5
LCD_CMD = 1 << 5
LCD_DATA = 2 << 5
LCD_SET = 3 << 5
LCD_GET = 4 << 5

# target is value to set
LCD_SET_CONTRAST = LCD_SET | (0 << 3)
LCD_SET_BRIGHTNESS = LCD_SET | (1 << 3)
LCD_SET_RESERVED0 = LCD_SET | (2 << 3)
LCD_SET_RESERVED1 = LCD_SET | (3 << 3)

# target is value to get
LCD_GET_FWVER = LCD_GET | (0 << 3)
LCD_GET_KEYS = LCD_GET | (1 << 3)
LCD_GET_CTRL = LCD_GET | (2 << 3)
LCD_GET_RESERVED1 = LCD_GET | (3 << 3)

# custom symbols
SMILE_SYMBOL = bytearray([0x00, 0x0a, 0x0a, 0x00, 0x11, 0x0e, 0x00, 0x00])


TYPE_VENDOR = libusb1.libusb_request_type.forward_dict['LIBUSB_TYPE_VENDOR']
REQUEST_GET_TYPE = TYPE_VENDOR | libusb1.LIBUSB_RECIPIENT_DEVICE | \
    libusb1.LIBUSB_ENDPOINT_IN


class LCD2USBNotFound(Exception):
    '''LCD2USB device not found'''

    def __str__(self):
        return 'Cound not find LCD2USB device.'


def find():
    '''find LCD2USB device'''

    context = usb1.USBContext()
    handle = context.openByVendorIDAndProductID(LCD2USB_VENDOR_ID,
                                                LCD2USB_PRODUCT_ID)
    return handle


class LCD(object):
    '''HD44780 based text LCD display supported with LCD2USB'''

    def __init__(self):
        self.device = find()
        if not self.device:
            raise LCD2USBNotFound()

        self.ctrl0, self.ctrl1 = {0: (False, False),
                                  1: (True, False),
                                  2: (True, True),
                                  }.get(self._get_controller())

        # to increase performance, a little buffer is being used to
        # collect command bytes of the same type before transmitting them
        self.BUFFER_MAX_CMD = 4  # current protocol supports up to 4 bytes
        self.buffer_current_type = -1  # nothing in buffer yet
        self.buffer_current_fill = 0  # -"-
        self.buffer = bytearray(self.BUFFER_MAX_CMD)

    @classmethod
    def find_or_die(cls):
        try:
            return cls()
        except LCD2USBNotFound, exc:
            print 'Error:', exc
            import sys
            sys.exit(1)

    def close(self):
        '''close usb device connection'''

        self.device.close()

    def info(self, verbose=True):
        '''print usb device info'''

        device = self.device.getDevice()
        bus = device.getBusNumber()
        dev = device.getDeviceAddress()
        if verbose:
            print 'Found LCD2USB device on bus %03d device %03d.' % (bus, dev)

        return bus, dev

    @property
    def __control(self):
        '''helper method'''
        return self.device._controlTransfer

    def echo(self, value):
        '''echo test

        send a number of 16 bit words to the lcd2usb interface
        and verify that they are correctly returned by the echo
        command. This may be used to check the reliability of
        the usb interfacing'''

        ret = usb1.create_binary_buffer(2)
        n_bytes = self.__control(REQUEST_GET_TYPE, LCD_ECHO, value, 0,
                                 ret, ctypes.sizeof(ret), 1000)
        if n_bytes < 0:
            print 'USB request failed!'
            return -1

        ret, = struct.unpack('H', ret.raw)  # unsigned short, size 2
        return ret

    def get(self, command):
        '''get a value from the lcd2usb interface'''

        buf = usb1.create_binary_buffer(2)

        # send control request and accept return value
        n_bytes = self.__control(REQUEST_GET_TYPE, command, 0, 0,
                                 buf, ctypes.sizeof(buf), 1000)
        if n_bytes < 0:
            print 'USB request failed!'
            return -1

        # low, high = struct.unpack('BB', buf.raw)  # 2 unsigned char
        # return low + 256 * high
        ret, = struct.unpack('H', buf.raw)
        return ret

    @property
    def version(self):
        '''firmware version of lcd2usb interface'''

        ver = self.get(LCD_GET_FWVER)

        if ver != -1:
            return (ver & 0xff, ver >> 8)
        return -1, -1

    def _get_controller(self):
        '''get the bit mask of installed LCD controllers

        0 = no lcd found,
        1 = single controller display,
        3 = dual controller display'''

        return self.get(LCD_GET_CTRL)

    @property
    def keys(self):
        '''state of the two optional buttons'''

        keymask = self.get(LCD_GET_KEYS)

        return bool(keymask & 1), bool(keymask & 2)

    def set(self, command, value):
        '''set a value in the LCD interface'''

        n_bytes = self.__control(TYPE_VENDOR, command, value, 0, 0, 0, 1000)
        if n_bytes < 0:
            print 'USB request failed!'
        return n_bytes

    def set_contrast(self, value):
        '''set contrast to a value between 0 and 255.

        Result depends display type'''

        return self.set(LCD_SET_CONTRAST, value)

    def set_brightness(self, value):
        '''set backlight brightness to a value between 0 (off) anf 255'''

        return self.set(LCD_SET_BRIGHTNESS, value)

    def clear(self):
        '''clear display'''

        self.command(0x01)  # clear display
        self.home()

    def command(self, command, ctrl=LCD_BOTH):
        '''see HD44780 datasheet for a command description'''

        # command format:
        # 7 6 5 4 3 2 1 0
        # C C C T T R L L
        #
        # TT = target bit map
        # R = reserved for future use, set to 0
        # LL = number of bytes in transfer - 1

        self._enqueue(LCD_CMD | ctrl, command)

    def _enqueue(self, command_type, value):
        '''enqueue a command into the buffer'''

        if self.buffer_current_type >= 0 and \
                self.buffer_current_type != command_type:
            self._flush()

        # add new item to buffer
        self.buffer_current_type = command_type
        self.buffer[self.buffer_current_fill] = value
        self.buffer_current_fill += 1

        # flush buffer if it's full
        if self.buffer_current_fill == self.BUFFER_MAX_CMD:
            self._flush()

    def _flush(self):
        '''flush command queue due to buffer overflow / content
        change or due to explicit request'''

        # anything to flush? ignore request if not
        if self.buffer_current_type == -1:
            return

        # build request byte
        request = self.buffer_current_type | (self.buffer_current_fill - 1)

        # fill value and index with buffer contents. endianess should IMHO not
        # be a problem, since usb_control_msg() will handle this.
        value = self.buffer[0] | (self.buffer[1] << 8)
        index = self.buffer[2] | (self.buffer[3] << 8)

        # send current buffer contents
        self._send(request, value, index)

        # buffer is now free again
        self.buffer_current_type = -1
        self.buffer_current_fill = 0

    def _send(self, request, value, index):
        '''send an usb control message'''
        n_bytes = self.__control(TYPE_VENDOR, request, value,
                                 index, 0, 0, 1000)
        if n_bytes < 0:
            print 'USB request failed!'
            return -1
        return 0

    def home(self):
        '''home display'''

        self.command(0x03)  # return home

    def write(self, data, column=None, row=None, ctrl=LCD_BOTH):
        '''write a data string to the display'''

        if isinstance(row, int) and isinstance(column, int):
            self.goto(column, row)

        if isinstance(data, str):
            data = bytearray(data)
        for char in data:
            self._enqueue(LCD_DATA | ctrl, char)

        self._flush()

    def write_char(self, char, column=None, row=None, ctrl=LCD_BOTH):
        '''write a char to the display'''

        self.write(bytearray([char]), column=column, row=row, ctrl=ctrl)

    def goto(self, column, row):
        '''set cursor on column(x) and row(y)'''

        address = {0: 0x80, 1: 0xc0, 2: 0x94, 3: 0xd4}

        self.command(address.get(row, 0x80) + column)

    def define_char(self, ascii, data):
        '''recording custom symbol to the HD44780 memory'''

        # try http://www.quinapalus.com/hd44780udg.html to design your chars

        base_address = 0x40 | (ascii << 3)
        self.command(base_address)
        self.write(data)

    def hello(self):
        '''display a hello screen on your lcd2usb device.

        this is useful for quick test your device'''

        self.clear()
        self.write('       WELCOME      ')
        self.write('    using LCD2USB   ', 0, 1)
        self.write('     with Python    ', 0, 2)
        self.write(' xieyanbo@gmail.com ', 0, 3)

        self.define_char(0, SMILE_SYMBOL)
        self.write_char(0, 0, 0)
        self.write_char(0, 19, 0)

    def fill(self, message, row_index=0, align='left'):
        if not isinstance(message, str):
            message = str(message)
        size = 20
        if len(message) > size:
            fillup = message[:size]
        else:
            if align == 'left':
                fillup = message.ljust(size)
            elif align == 'center':
                fillup = message.center(size)
            elif align == 'right':
                fillup = message.rjust(size)
            else:
                fillup = message.ljust(size)
        self.write(fillup, 0, row_index)

    def fill_center(self, message, row_index=0):
        self.fill(message, row_index, align='center')

    def fill_right(self, message, row_index=0):
        self.fill(message, row_index, align='right')


def test():
    '''Test the lcd2usb device and show a demo.

    If you need a quickly running test for your device, use this:

        python -m lcd2usb
    '''

    lcd = LCD.find_or_die()
    lcd.info()
    print 'echo 1234, get:', lcd.echo(1234)
    print 'version:', '%s.%s' % lcd.version
    print 'ctrl0:', lcd.ctrl0, 'ctrl1:', lcd.ctrl1
    print 'keys on?', lcd.keys

    lcd.hello()
    return lcd


if __name__ == '__main__':
    test()
