import os
import sys

class Parser:
    REG_SEG = {
        'local': 'LCL',
        'argument': 'ARG',
        'this': 'THIS',
        'that': 'THAT',
    }
    UNARY_SEG = ['constant', 'temp']
    REQ_JMP = ['eq', 'lt', 'gt']

    def __init__(self, filename):
        self.filename = filename
        self.logical_comp_ctr = -1
        self.build = {
            'push': self._build_mem_ops,
            'pop': self._build_mem_ops,
            'add': self._build_arith_ops,
            'sub': self._build_arith_ops,
            'eq': self._build_arith_ops,
            'lt': self._build_arith_ops,
            'gt': self._build_arith_ops,
            'neg': self._build_arith_ops,
            'and': self._build_arith_ops,
            'or': self._build_arith_ops,
            'not': self._build_arith_ops,
        }

    def _build_arith_ops(self, action):
        if action not in Parser.REQ_JMP:
            return {
                'action': action
            }

        self.logical_comp_ctr += 1
        return {
            'action': action,
            'attrs': {
                'ctr': self.logical_comp_ctr
            }
        }

    def _build_mem_ops(self, action, segment, i):
        base = {
            'action': action,
            'segment': segment,
        }
        if segment in Parser.REG_SEG:
            return {
                **base,
                'segment': 'regular',
                'attrs': {
                    'segment': Parser.REG_SEG[segment],
                    'i': i,
                },
            }
        if segment in Parser.UNARY_SEG :
            return {
                **base,
                'attrs': {
                    'i': i,
                },
            }
        if segment == 'static':
            return {
                **base,
                'attrs': {
                    'filename': self.filename,
                    'i': i,
                },
            }
        if segment == 'pointer':
            return {
                **base,
                'attrs': {
                    'ptr_seg': 'THIS' if i == '0' else 'THAT'
                }
            }

    def _clean(self, line):
        return line.split('//')[0].rstrip().lstrip()

    def parse(self, line):
        line = self._clean(line)
        if not line:
            return {'action': None}

        action, *attrs = line.split(' ')
        return self.build[action](action, *attrs)


asm = {
    'not': (
        "@SP\nA=M-1\nM=!M"
    ),
    'or': (
        "@SP\nAM=M-1\nD=M\nA=A-1\nM=M|D"
    ),
    'and': (
        "@SP\nAM=M-1\nD=M\nA=A-1\nM=M&D"
    ),
    'neg': (
        "@SP\nA=M-1\nM=-M"
    ),
    'gt': (
        "@SP\nAM=M-1\nD=M\nA=A-1\nD=D-M\n"
        "@32767\nA=A+1\nD=D&A\n@logi_gt_{ctr}\n"
        "D;JEQ\nD=-1\n(logi_gt_{ctr})\n@SP\nA=M-1\nM=D"
    ),
    'lt': (
        "@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n"
        "@32767\nA=A+1\nD=D&A\n@logi_lt_{ctr}\n"
        "D;JEQ\nD=-1\n(logi_lt_{ctr})\n@SP\nA=M-1\nM=D"
    ),
    'add': (
        "@SP\nAM=M-1\nD=M\nA=A-1\nM=M+D"
    ),
    'sub': (
        "@SP\nAM=M-1\nD=M\nA=A-1\nM=M-D"
    ),
    'eq': (
        "@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n"
        "@logi_eq_{ctr}\nD;JEQ\nD=-1\n"
        "(logi_eq_{ctr})\n@SP\nA=M-1\nM=!D"
    ),
    'pop_regular': (
        "@{i}\nD=A\n@{segment}\nD=D+M\n"
        "@R13\nM=D\n@SP\nAM=M-1\nD=M\n"
        "@R13\nA=M\nM=D"
    ),
    'pop_static': (
        "@SP\nAM=M-1\nD=M\n"
        "@{filename}.{i}\nM=D"
    ),
    'pop_temp': (
        "@5\nD=A\n@{i}\nD=D+A\n@R13\nM=D\n"
        "@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D"
    ),
    'pop_pointer': (
        "@{ptr_seg}\nD=A\n@R13\nM=D\n"
        "@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D"
    ),
    'push_regular': (
        "@{i}\nD=A\n@{segment}\nA=D+M\nD=M\n"
        "@SP\nA=M\nM=D\n@SP\nM=M+1"
    ),
    'push_constant': (
        "@{i}\nD=A\n@SP\nA=M\nM=D\n"
        "@SP\nM=M+1"
    ),
    'push_static': (
        "@{filename}.{i}\nD=M\n"
        "@SP\nA=M\nM=D\n@SP\nM=M+1"
    ),
    'push_temp': (
        "@5\nD=A\n@{i}\nA=D+A\nD=M\n"
        "@SP\nA=M\nM=D\n@SP\nM=M+1"
    ),
    'push_pointer': (
        "@{ptr_seg}\nD=M\n@SP\nA=M\nM=D\n"
        "@SP\nM=M+1"
    ),
}


class Translator:
    MEM_OPS = ['pop', 'push']
    NO_ATTRS = ['add', 'sub', 'neg', 'and', 'or', 'not']
    def __init__(self, parser):
        self.parser = parser

    def translate(self, line):
        data = self.parser.parse(line)
        if data['action'] is None:
            return ''
        else:
            ret = f"// {line}"
            key = data['action']
            if data['action'] in Translator.MEM_OPS:
                key = f"{data['action']}_{data['segment']}"
            if data['action'] in Translator.NO_ATTRS:
                return ret + asm[key]
            return ret + asm[key].format(**data['attrs'])

if __name__ == '__main__':
    path = sys.argv[1]
    tar = os.path.join(os.path.dirname(__file__), path)
    loc = os.path.join(os.path.dirname(__file__), path[:-2] + 'asm')
    filename = tar.split('/')[-1].split('.')[0]
    parser = Parser(filename)
    trs = Translator(parser)
    with open(loc, 'w') as outfile:
        with open(tar, 'r') as infile:
            for line in infile:
                conv = trs.translate(line)
                if conv:
                    outfile.write(conv+'\n')
