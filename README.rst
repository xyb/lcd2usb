LCD2USB's Python Library

home: http://github.com/xyb/lcd2usb

PyPI: http://pypi.python.org/pypi/lcd2usb

Introduce
=========

The LCD2USB's Python Library is a Pure-python wrapper for LCD2USB_ which
provide a simple way to control your LCD2USB display device. LCD2USB_ is a
open source/open hardware project to connect HD44780 based text LCD displays
to various PCs via USB.

Usage
=====

Connect a lcd2usb device is easy::

    >>> from lcd2usb import LCD
    >>> lcd = LCD()
    >>> lcd.info()
    Found LCD2USB device on bus 004 device 004.

Get lcd2usb firmware version::

    >>> lcd.version
    (1, 9)

Write something on the screen::

    >>> lcd.write('Hello, LCD2USB!')

Clean screen and wirte some on the 2nd row::

    >>> lcd.clear()
    >>> lcd.goto(0, 1)
    >>> lcd.write('Flying with PYTHON')

Or simpler::

    >>> lcd.write('Flying with PYTHON', 0, 1)

Define a custom smile symbol and display it on the center of first row
(on a 4x20 display)::

    >>> from lcd2usb import SMILE_SYMBOL
    >>> lcd.define_char(0, SMILE_SYMBOL)
    >>> lcd.write('\0', 9, 0)

That it!

If you need a quickly running test for your device, use this::

    python -m lcd2usb

Requirements
============

- Python_ 2.5+ required

- ctypes_ (included in Python 2.5+)

- libusb-1.0_

- python-libusb1_

Installation
============

Installation is done just as for any other Python library. Using the ``pip`` or ``easy_install`` command from setuptools is the easiest::

    pip install lcd2usb

Or::

    easy_install install lcd2usb


.. _LCD2USB: http://www.harbaum.org/till/lcd2usb

.. _Python: http://www.python.org/

.. _ctypes: http://python.net/crew/theller/ctypes/

.. _libusb-1.0: http://www.libusb.org/wiki/libusb-1.0

.. _python-libusb1: http://github.com/vpelletier/python-libusb1
