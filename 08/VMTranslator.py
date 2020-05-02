import glob
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

    def __init__(self, filename=None):
        self.context = {
            'file': filename,
            'func': '',
            'call_ctr': 0,
        }
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
            'label': self._build_branch_ops,
            'if-goto': self._build_branch_ops,
            'goto': self._build_branch_ops,
            'function': self._build_function_ops,
            'return': self._build_function_ops,
            'call': self._build_function_ops,
        }

    def set_filename(self, filename):
        self.context['file'] = filename

    def _build_function_ops(self, action, name=None, count=None):
        if action == 'return':
            return {
                'action': action
            }

        # Set context for func name
        if action == 'function':
            self.context['func'] = name
            self.context['call_ctr'] = 0
            return {
                'action': action,
                'attrs': {
                    'name': name,
                    'count': count,
                }
            }

        if action == 'call':
            self.context = {
                **self.context,
                'call_ctr': self.context['call_ctr']+1
            }

        return {
            'action': action,
            'attrs': {
                'callee': name,
                'count': count,
                'caller': self.context['func'],
                'call_ctr': self.context['call_ctr'],
            }
        }

    def _build_branch_ops(self, action, name):
        return {
            'action': action,
            'attrs': {
                'func': self.context['func'],
                'name': name
            }
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
                    'filename': self.context['file'],
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
        return {
            **self.build[action](action, *attrs),
            'line': line
        }

asm = {
    'bootstrap': (
        "@256\nD=A\n@SP\nM=D\n"
        "D=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        "@LCL\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        "@ARG\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        "@THIS\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        "@THAT\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        "@5\nD=A\n@0\nD=D+A\n@SP\nD=M-D\n"
        "@ARG\nM=D\n@Sys.init\n0;JMP"
    ),
    'call': (
        "@{caller}$ret.{call_ctr}\n"
        "D=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        "@LCL\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        "@ARG\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        "@THIS\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        "@THAT\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        "@5\nD=A\n@{count}\nD=D+A\n@SP\nD=M-D\n"
        "@ARG\nM=D\n@{callee}\n0;JMP\n"
        "({caller}$ret.{call_ctr})"
    ),
    'return': (
        "@5\nD=A\n@LCL\nA=M-D\nD=M\n@R13\nM=D\n"
        "@SP\nA=M-1\nD=M\n@ARG\nA=M\nM=D\n"
        "@ARG\nD=M+1\n@SP\nM=D\n"
        "@LCL\nAM=M-1\nD=M\n@THAT\nM=D\n"
        "@LCL\nAM=M-1\nD=M\n@THIS\nM=D\n"
        "@LCL\nAM=M-1\nD=M\n@ARG\nM=D\n"
        "@LCL\nAM=M-1\nD=M\n@LCL\nM=D\n"
        "@R13\nA=M\n0;JMP"
    ),
    'function': (
        "({name})\n@SP\nD=M\n"
        "@LCL\nM=D\n@{count}\nD=A\n"
        "@SP\nM=M+D\n@{name}$lcl_init_ignore\nD;JEQ\n"
        "@R13\nM=D\n@R14\nM=0\n({name}$lcl_init)\n"
        "@R14\nD=M\n@LCL\nA=D+M\nM=0\n@R14\n"
        "MD=D+1\n@R13\nD=D-M\n@{name}$lcl_init\nD;JLT\n"
        "({name}$lcl_init_ignore)"
    ),
    'goto': (
        "@{func}${name}\n0;JMP"
    ),
    'if-goto': (
        "@SP\nAM=M-1\nD=M\n"
        "@{func}${name}\nD;JNE"
    ),
    'label': (
        "({func}${name})"
    ),
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
    NO_ATTRS = ['add', 'sub', 'neg', 'and', 'or', 'not', 'return']
    def __init__(self, parser):
        self.parser = parser

    def translate(self, line):
        data = self.parser.parse(line)
        if data['action'] is None:
            return ''
        else:
            ret = f"// {data['line']}\n"
            key = data['action']
            if data['action'] in Translator.MEM_OPS:
                key = f"{data['action']}_{data['segment']}"
            if data['action'] in Translator.NO_ATTRS:
                return ret + asm[key]
            return ret + asm[key].format(**data['attrs'])

def translate_dir(path):
    outname = f"{path.split('/')[-1]}.asm"
    loc = os.path.join(os.path.dirname(__file__), path, outname)
    parser = Parser()
    trs = Translator(parser)
    with open(loc, 'w') as outfile:
        outfile.write(asm['bootstrap']+'\n')
        for name in glob.glob(f'{path}/*.vm'):
            parser.set_filename(name.split('/')[-1][:-3])
            with open(name, 'r') as infile:
                for line in infile:
                    conv = trs.translate(line)
                    if conv:
                        outfile.write(conv+'\n')

def translate_file(path):
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

if __name__ == '__main__':
    path = sys.argv[1]
    tar = os.path.join(os.path.dirname(__file__), path)
    if os.path.isdir(tar):
        translate_dir(tar)
    else:
        translate_file(path)
