#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Helper script to start pyilper from package directory
#
# 01.03.2018 jsi
# - consider the required python version specified in pilcore.py
# 21.03.2026 jsi
# - refactoring of global variables
#
import sys
import os
import warnings
from pyilper.pilglobals import PILGLOBALS

if sys.version_info < ( PILGLOBALS.Python_Required_Major, PILGLOBALS.Python_Required_Minor):
    # python too old, kill the script
    sys.exit("This script requires Python "+str(PYTHON_REQUIRED_MAJOR)+"."+str(PYTHON_REQUIRED_MINOR)+" or newer!")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
warnings.simplefilter("default")
from pyilper import main
main()
