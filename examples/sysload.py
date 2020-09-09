#!/usr/bin/env python
# encoding: utf8

'''sysload.py - display system load average
'''

import re
import subprocess
import time

from lcd2usb import LCD

RE_UPTIME = re.compile(r'(.*?)\s+up\s+(.*?),\s+(\d+) users?,\s+'
                       r'load averages?: (\d+\.\d+),?'
                       r'\s+(\d+\.\d+),?\s+(\d+\.\d+)')


def load_uptime():
    info = subprocess.check_output('uptime')
    _, duration, users, avg1, avg5, avg15 = RE_UPTIME.match(str(info)).groups()
    days = '0'
    hours = '0'
    mins = '0'
    if 'day' in duration:
        match = re.search(r'([0-9]+)\s+day', duration)
        days = str(int(match.group(1)))
    if ':' in duration:
        match = re.search(r'([0-9]+):([0-9]+)', duration)
        hours = str(int(match.group(1)))
        mins = str(int(match.group(2)))
    if 'min' in duration:
        match = re.search(r'([0-9]+)\s+min', duration)
        mins = str(int(match.group(1)))
    return int(days), int(hours), int(mins), int(users), \
        float(avg1), float(avg5), float(avg15)


class Bar(object):
    HEIGHT = 8

    def __init__(self, size):
        self.lcd = lcd
        self.size = size
        self.data = [0] * size

    def define(self, lcd):
        # define bar symbols
        bar = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        for i in range(8):
            bar[self.HEIGHT - i - 1] = 0xff
            lcd.define_char(i, bar)

    def update(self, number):
        self.data.append(number)
        self.data = self.data[1:]
        return self.get_value()

    def get_value(self):
        max_value = max(self.data)
        mapping = [int((self.HEIGHT - 1) * i / max_value) for i in self.data]
        return ''.join([chr(i) for i in mapping])


def main(lcd):
    bar = Bar(10)
    bar.define(lcd)
    lcd.clear()
    n = 0
    while True:
        days, hours, mins, users, avg1, avg5, avg15 = load_uptime()
        import datetime
        lcd.home()
        lcd.fill(str(datetime.datetime.now())[:19], 0)

        if avg1 < 10:
            load = '%.2f' % avg1
        elif avg1 < 100:
            load = '%.1f' % avg1
        else:
            load = '%.0f' % avg1
        if n % 5 == 0:
            load_bar = bar.update(avg1)
        else:
            load_bar = bar.get_value()
        n += 1
        load_row = 'LOAD %s %s' % (load_bar, load)
        lcd.fill(load_row, 1)

        if days:
            row2 = 'UP %d Days' % days
        elif hours:
            row2 = 'UP %d Hours' % hours
        else:
            row2 = 'UP %d Mins' % mins
        row2 += ', %d Users' % users
        lcd.fill(row2, 2)
        time.sleep(2)


if __name__ == '__main__':
    lcd = LCD.find_or_die()
    lcd.info()
    try:
        main(lcd)
    except KeyboardInterrupt:
        pass
