#!/usr/bin/python

# requirements
from termcolor import *

# print helper
def cprint(status, phase, message):
    if status:
        print colored(phase + "> ", "blue", attrs=["bold"]) + message
    else:
        print colored(phase + "> ", "red", attrs=["bold"]) + message
