# HackSysExtreme Vulnerable Driver Kernel Exploit (x64 Use After Free/SMEP Enabled)
# Author: Connor McGarr

import struct
import sys
import os
from ctypes import *

kernel32 = windll.kernel32
ntdll = windll.ntdll
psapi = windll.psapi
