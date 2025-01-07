from setuptools import setup
import os

long_description = open(os.path.join(os.path.dirname(__file__), 'README.rst')
                        ).read()

setup(
    name='lcd2usb',
    description=long_description.split('\n')[0],
    long_description='.. contents::\n\n' + long_description,
    keywords='usb lcd lcd2usb',
    version='1.4',
    author='Xie Yanbo',
    author_email='xieyanbo@gmail.com',
    url='http://github.com/xyb/lib2usb',
    license='New BSD',
    platforms=['any'],
    py_modules=['lcd2usb'],
    install_requires=['libusb1'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Hardware :: Hardware Drivers',
    ],
)
