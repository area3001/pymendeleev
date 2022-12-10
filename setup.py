#!/usr/bin/env python

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='pymendeleev',
    version='0.0.1',
    author='Bert Outtier',
    author_email='outtierbert@gmail.com',
    url='https://github.com/area3001/pymendeleev',
    description='Python library for Mendeleev serial protocol',
    download_url='https://github.com/area3001/pymendeleev',
    license='MIT',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['mendeleev'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Home Automation',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'pyserial-asyncio==0.6',
        'scapy==2.4.5',
        'asyncio-mqtt==0.16.1',
        'aioconsole==0.5.1'
    ],
    scripts=[
        'bin/mqtt2mendeleev',
        'bin/artnet2mqtt',
    ],
)
