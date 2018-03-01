#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Helper script to start pyilper from package directory
#
# 01.03.2018 jsi
# - consider the required python version specified in pilcore.py
#
import sys
import os
from pyilper.pilcore import PYTHON_REQUIRED_MAJOR, PYTHON_REQUIRED_MINOR

if sys.version_info < ( PYTHON_REQUIRED_MAJOR, PYTHON_REQUIRED_MINOR):
    # python too old, kill the script
    sys.exit("This script requires Python "+str(PYTHON_REQUIRED_MAJOR)+"."+str(PYTHON_REQUIRED_MINOR)+" or newer!")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pyilper import main
main()
