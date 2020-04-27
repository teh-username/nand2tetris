import sys

from enum import Enum

class ATTR_TYPE(Enum):
    COMMENT = 0
    A_INST = 1
    C_INST = 2
    LABEL = 3
    EMPTY = 4

class Parser:
    def _build_return(self, attr_type, attrs={}):
        return {
            'type': attr_type,
            'attrs': {
                **attrs
            }
        }

    def _parse_c_inst(self, line):
        (dest, jmp) = (None, None)
        eq_split = line.split('=')
        if len(eq_split) > 1:
            dest=eq_split[0]
        jmp_split = eq_split[-1].split(';')
        if len(jmp_split) > 1:
            jmp=jmp_split[-1]
        return {
            'dest': dest,
            'comp': jmp_split[0],
            'jmp': jmp
        }

    def parse(self, line):
        line = line.rstrip().lstrip()
        if '' == line:
            return self._build_return(ATTR_TYPE.EMPTY)
        if '//' == line[:2]:
            return self._build_return(ATTR_TYPE.COMMENT)

        line = line.split('//')[0].rstrip()
        if '@' == line[0]:
            return self._build_return(
                ATTR_TYPE.A_INST,
                {'ref': line[1:]}
            )
        if '(' == line[0]:
            return self._build_return(
                ATTR_TYPE.LABEL,
                {'name': line[1:-1]}
            )
        return self._build_return(
            ATTR_TYPE.C_INST,
            self._parse_c_inst(line)
        )

class Assembler:
    symbols = {
        'SP': 0,
        'LCL': 1,
        'ARG': 2,
        'THIS': 3,
        'THAT': 4,
        'R0': 0,
        'R1': 1,
        'R2': 2,
        'R3': 3,
        'R4': 4,
        'R5': 5,
        'R6': 6,
        'R7': 7,
        'R8': 8,
        'R9': 9,
        'R10': 10,
        'R11': 11,
        'R12': 12,
        'R13': 13,
        'R14': 14,
        'R15': 15,
        'SCREEN': 16384,
        'KBD': 24576,
    }

    bits = {
        ATTR_TYPE.C_INST: {
            'comp': {
                '0':   '0101010',
                '1':   '0111111',
                '-1':  '0111010',
                'D':   '0001100',
                'A':   '0110000',
                'M':   '1110000',
                '!D':  '0001101',
                '!A':  '0110001',
                '!M':  '1110001',
                '-D':  '0001111',
                '-A':  '0110011',
                '-M':  '1110011',
                'D+1': '0011111',
                'A+1': '0110111',
                'M+1': '1110111',
                'D-1': '0001110',
                'A-1': '0110010',
                'M-1': '1110010',
                'D+A': '0000010',
                'D+M': '1000010',
                'D-A': '0010011',
                'D-M': '1010011',
                'A-D': '0000111',
                'M-D': '1000111',
                'D&A': '0000000',
                'D&M': '1000000',
                'D|A': '0010101',
                'D|M': '1010101',
            },
            'jmp': {
                None: '000',
                'JGT': '001',
                'JEQ': '010',
                'JGE': '011',
                'JLT': '100',
                'JNE': '101',
                'JLE': '110',
                'JMP': '111',
            },
            'dest': {
                None: '000',
                'M': '001',
                'D': '010',
                'MD': '011',
                'A': '100',
                'AM': '101',
                'AD': '110',
                'AMD': '111',
            }
        }
    }


    def __init__(self, filename, parser):
        self.filename = filename
        self.parser = parser
        self.cur_reg = 16

    def _inc_line_number(self, ln, ln_type):
        if ln_type['type'] == ATTR_TYPE.A_INST:
            return ln+1
        if ln_type['type'] == ATTR_TYPE.C_INST:
            return ln+1
        return ln

    def _build_symbol_table(self):
        ln = 0
        with open(self.filename, 'r') as infile:
            for line in infile:
                line = self.parser.parse(line)
                ln = self._inc_line_number(ln, line)
                if line['type'] == ATTR_TYPE.LABEL:
                    Assembler.symbols[
                        line['attrs']['name']
                    ] = ln

    def _to_bits(self, line):
        if line['type'] == ATTR_TYPE.C_INST:
            dst = Assembler.bits[ATTR_TYPE.C_INST]['dest'][line['attrs']['dest']]
            cop = Assembler.bits[ATTR_TYPE.C_INST]['comp'][line['attrs']['comp']]
            jmp = Assembler.bits[ATTR_TYPE.C_INST]['jmp'][line['attrs']['jmp']]
            return '111' + cop + dst + jmp

        if line['type'] == ATTR_TYPE.A_INST:
            ref = line['attrs']['ref']
            if ref.isdigit():
                ref = int(ref)
                return '0' + bin(ref)[2:].rjust(15, '0')

            if ref not in Assembler.symbols:
                Assembler.symbols[ref] = self.cur_reg
                self.cur_reg += 1

            return '0' + bin(Assembler.symbols[ref])[2:].rjust(15, '0')

    def translate(self):
        self._build_symbol_table()
        with open('out.hack', 'w') as outfile:
            with open(self.filename, 'r') as infile:
                for line in infile:
                    line = self.parser.parse(line)
                    if line['type'] == ATTR_TYPE.C_INST or line['type'] == ATTR_TYPE.A_INST:
                        outfile.write(self._to_bits(line) + '\n')

if __name__ == '__main__':
    file = sys.argv[1]
    assembler = Assembler(
        file,
        Parser()
    )

    assembler.translate()
