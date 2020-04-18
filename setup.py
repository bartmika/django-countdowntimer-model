#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import io
import re
import os
import sys


def readme():
    with io.open("README.rst", "r", encoding="utf-8") as my_file:
        return my_file.read()

setup(
    name='django-countdowntimer_model',
    version='0.0.3',
    url='https://github.com/bartmika/django-countdowntimer-model',
    license='BSD 2-Clause License',
    description="Abstract countdown timer model to use in your Django projects.",
    long_description=readme(),
    author='Bartlomiej Mika',
    author_email='bart@mikasoftware.com',
    packages=find_packages(),
    install_requires=[
        'django>=3.0.5',
        'pytz>=2019.3'
    ],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities'
    ],
    keywords='library countdown timer elapsed remaining time django timedelta helper',
)
