#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Helper script to start pyilper from package directory
#
import sys
import os

if sys.version_info < ( 3, 4):
    # python too old, kill the script
    sys.exit("This script requires Python 3.4 or newer!")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pyilper import main
main()
