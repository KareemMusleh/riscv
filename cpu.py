#!/usr/bin/env python

from elftools.elf.elffile import ELFFile
import glob
import struct
from enum import Enum

regs = [0] * 33
pc = 32

MAX64 = 0xffffffffffffffff
MAX64 = 0xffffffff
BASE_ADDR = 0x80000000
memory = bytearray(b'\00' * 0x8000)

class OPCODE(Enum): # Source: search for RV32I Base Instruction Set in the unpriv spec
    LUI = 0b0110111 # Load Upper Immediate
    AUIPC = 0b0010111 # Add Upper Immediate to PC
    JAL = 0b1101111 # Jump And Link
    JALR = 0b1100111 # Jump And Link Register
    BRANCH = 0b1100011
    IMM = 0b010011
    SYSTEM = 0b1110011

class Funct3(Enum):
    # copied from geohotz impl
    ADD = SUB = ADDI = 0b000
    SLLI = 0b001
    SLT = SLTI = 0b010
    SLTU = SLTIU = 0b011

    XOR = XORI = 0b100
    SRL = SRLI = SRA = SRAI = 0b101
    OR = ORI = 0b110
    AND = ANDI = 0b111

    BEQ = 0b000
    BNE = 0b001
    BLT = 0b100
    BGE = 0b101
    BLTU = 0b110
    BGEU = 0b111

    LB = SB = 0b000
    LH = SH = 0b001
    LW = SW = 0b010
    LBU = 0b100
    LHU = 0b101

def load_seg(seg):
    addr, data = seg.header.p_paddr, seg.data()
    addr -= BASE_ADDR
    global memory
    assert 0 <= addr < len(memory) - len(data)
    memory[addr: addr + len(data)] = data

def get_inst():
    addr = regs[pc] - BASE_ADDR
    assert 0 <= addr < len(memory) - 4
    return struct.unpack('<I', memory[addr: addr + 4])[0]

def step():
    inst = get_inst()
    def get_part(start, end): # this is inclusive
        return ((((1 << (end - start + 1)) - 1) << start) & inst) >> start
    opcode = OPCODE(get_part(0, 6))
    rd = get_part(7, 11)

    print(hex(inst), opcode)
    # imm_x is the imm for the x type of instruction
    imm_j = get_part(21, 30) << 1| get_part(20, 20) << 11 | get_part(12, 19) << 12 | get_part(30, 31)<<20
    imm_i = get_part(20, 31)
    imm_s = get_part(7, 11) | get_part(25, 31) << 4
    imm_b = get_part(8, 11) << 1 | get_part(25, 30) << 5 | get_part(7, 7) << 10 | get_part(31, 31) << 11

    funct3 = get_part(12, 14)
    rs1 = get_part(15, 19)
    rs2 = get_part(20, 24)
    if opcode == OPCODE.JAL:
        regs[pc] += imm_j
        return True
    if opcode == OPCODE.IMM:
        regs[pc] += 4
        if Funct3(funct3) == Funct3.ADD:
            regs[rd] = imm_i + regs[rs1]
        # if Funct3(funct3) == Funct3.SUB:
        return True
    if opcode == OPCODE.SYSTEM:
        regs[pc] += 4
        return True
    if opcode == OPCODE.BRANCH:
        regs[pc] += 4
        if funct3 == Funct3.BEQ:
            if regs[rs1] == regs[rs2]:
                regs[pc] -= 4 + imm_b
                print(hex(imm_b))
        if funct3 == Funct3.BNE:
            if regs[rs1] != regs[rs2]:
                regs[pc] -= 4 + imm_b
                print(hex(imm_b))
        if funct3 == Funct3.BLT:
            if regs[rs1] < regs[rs2]:
                regs[pc] -= 4 + imm_b
        if funct3 == Funct3.BLTU:
            if regs[rs1] < regs[rs2]:
                regs[pc] -= 4 + imm_b
        if funct3 == Funct3.BGE:
            if regs[rs1] >= regs[rs2]:
                regs[pc] -= 4 + imm_b
        if funct3 == Funct3.BGEU:
            if regs[rs1] >= regs[rs2]:
                regs[pc] -= 4 + imm_b
        return True
    return False

if __name__ == "__main__":
    # implementing RV64 user-level, integer only
    # virtual memory is disabled, only core 0 boots up
    for file in glob.glob('riscv-tests/isa/rv64ui-p*'):
        if file.endswith('.dump'): continue
        with open(file, 'rb') as f:
            print(f'test {file}: ', end='\n')
            e = ELFFile(f)
            for seg in e.iter_segments():
                if seg.header.p_paddr == 0: continue # .riscv.attributes
                load_seg(seg)
            regs[pc] = BASE_ADDR
            while step(): continue
            quit()
