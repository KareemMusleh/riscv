from elftools.elf.elffile import ELFFile
import glob
MAX64 = 0xffffffffffffffff
MAX64 = 0xffffffff
BASE_ADDRESS = 0x80000000

if __name__ == "__main__":
    # implementing RV64 user-level, integer only
    # virtual memory is disabled, only core 0 boots up
    for file in glob.glob('riscv-tests/isa/rv64ui-p*'):
        if file.endswith('.dump'): continue
        with open(file, 'rb') as f:
            print(f'test {file}: ', end='\n')
            e = ELFFile(f)
            for s in e.iter_segments():
                
                print(hex(s.header.p_paddr), s.data())
        quit()
