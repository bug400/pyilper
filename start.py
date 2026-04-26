#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Helper script to start pyilper from package directory
#
# 01.03.2018 jsi
# - consider the required python version specified in pilcore.py
# 21.03.2026 jsi
# - refactoring of global variables
# 21.04.2026 jsi
# - removed Python version check, now in pilglobals.py
#
import sys
import os
import warnings

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
warnings.simplefilter("default")
from pyilper.__main__ import start
start()

