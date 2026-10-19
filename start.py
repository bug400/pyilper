#!/usr/bin/env python

""" start.py: run pyilper as a module located in the current directory """
import runpy
ret=runpy.run_module("pyilper",run_name="__main__",alter_sys=True)
