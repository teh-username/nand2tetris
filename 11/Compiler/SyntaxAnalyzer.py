import re

from SymbolTable import SymbolTable
from CodeGen import CodeGen

class Tokenizer:
    lex_types = [
        'keyword',
        'symbol',
        'stringConstant',
        'identifier',
        'integerConstant',
    ]

    special_chars = {
        '>': '&gt;',
        '<': '&lt;',
        '&': '&amp;',
        '"': '&quot;',
    }

    def __init__(self, filename):
        # Matching Groups: keywords, symbols, String constant, identifier, integer constants
        self.p = re.compile(r"(?:\/\*\*[\S\s]*?\*\/)|(?:\/\/.*$)|(\bclass\b|\bconstructor\b|\bfunction\b|\bmethod\b|\bfield\b|\bstatic\b|\bvar\b|\bint\b|\bchar\b|\bboolean\b|\bvoid\b|\btrue\b|\bfalse\b|\bnull\b|\bthis\b|\blet\b|\bdo\b|\bif\b|\belse\b|\bwhile\b|\breturn\b)|(\{|\}|\(|\)|\[|\]|\.|\,|\;|\+|\-|\*|\/|\&|\||\<|\>|\=|\~)|((?<=\").*(?=\"))|((?:[_a-zA-Z]+)(?:[_a-zA-Z0-9]?))|([0-9]+)", re.MULTILINE)
        self.tokens = []
        with open(filename, 'r') as infile:
            self._tokenize_file(infile.read())

    def get_token(self):
        return self.tokens[0]

    def advance(self):
        self.tokens = self.tokens[1:]

    def _add_token(self, const, lexType):
        self.tokens.append(
            {
                'const': const,
                'type': lexType
            }
        )

    def _tokenize_file(self, text):
        matches = self.p.finditer(text)
        for match in matches:
            for idx, iden in enumerate(self.lex_types):
                tar = match.groups()[idx]
                if tar is None:
                    continue
                if tar in self.special_chars:
                    self._add_token(
                        self.special_chars[tar],
                        iden
                    )
                else:
                    self._add_token(tar, iden)

class CompilationEngine:
    def __init__(self, path, filename, symbol_table, code_generator):
        self.flow_ctr = {
            'while': 0,
            'if': 0,
        }
        self.symbols = symbol_table
        self.gen = code_generator
        self.tokenizer = Tokenizer(f"{path}/{filename}.jack")
        self.class_name = filename
        self.cur_token = None
        self.compileClass()

    def _expectExact(self, expected, attr, strict=True, parentTag=None):
        token = self.tokenizer.get_token()
        if token[attr] != expected:
            if strict:
                raise Exception(f"Expected {expected}, got {token[attr]}")
            return False
        self.cur_token = token
        self.tokenizer.advance()
        return True

    def _expectChoices(self, expected, attr, strict=True, parentTag=None):
        token = self.tokenizer.get_token()
        for idx, expect in enumerate(expected):
            if token[attr[idx]] == expect:
                self.cur_token = token
                self.tokenizer.advance()
                return True
        if strict:
            raise Exception(f"Expected either {expected}, got {token}")
        return False

    def compileKeywordConstants(self, strict=True, parentTag=None):
        return self._expectChoices(
            ['true', 'false', 'null', 'this'],
            ['const', 'const', 'const', 'const'],
            strict,
            parentTag
        )

    def compileUnaryOp(self, strict=True, parentTag=None):
        return self._expectChoices(
            ['-', '~'],
            ['const', 'const'],
            strict,
            parentTag
        )

    def compileExpressionList(self):
        ctr = 0
        if not self.compileExpression():
            return ctr
        ctr += 1
        while self._expectExact(',', 'const', False):
            ctr += 1
            self.compileExpression()
        return ctr

    def compileExpression(self):
        if not self.compileTerm():
            return False
        while self.compileOp(False):
            op = self.cur_token['const']
            self.compileTerm()
            self.gen.write_arith(op)
        return True

    def compileTerm(self):
        if self._expectExact('(', 'const', False, 'term'):
            self.compileExpression()
            self._expectExact(')', 'const')
            return True
        if self.compileKeywordConstants(False, 'term'):
            keyword = self.cur_token['const']
            if keyword == 'true':
                self.gen.write_push('constant', 0)
                self.gen.write_arith('not')
            elif keyword == 'false':
                self.gen.write_push('constant', 0)
            elif keyword == 'this':
                self.gen.write_push('pointer', 0)
            elif keyword == 'null':
                self.gen.write_push('constant', 0)
            return True
        if self._expectExact('stringConstant', 'type', False, 'term'):
            str = self.cur_token['const']
            # Create String
            self.gen.write_push('constant', len(str))
            self.gen.write_call('String.new', 1)
            for c in str:
                self.gen.write_push('constant', ord(c))
                self.gen.write_call('String.appendChar', 2)
            # Append each char
            return True
        if self._expectExact('integerConstant', 'type', False, 'term'):
            self.gen.write_push('constant', self.cur_token['const'])
            return True
        if self.compileUnaryOp(False, 'term'):
            op = self.cur_token['const']
            self.compileTerm()
            if op == '-':
                self.gen.write_arith('neg')
            else:
                self.gen.write_arith('not')
            return True
        # If we're here, lookahead to determine which is which
        # varName
        if self._expectExact('identifier', 'type', False, 'term'):
            iden = self.cur_token['const']
            if self._expectExact('[', 'const', False):
                iden_sym = self.symbols.get(iden)
                # identifier[]
                # push base addr of arr
                self.gen.write_push(
                    iden_sym['category'],
                    iden_sym['idx']
                )
                self.compileExpression()
                self.gen.write_arith('+')
                self._expectExact(']', 'const')
                # pop computed exp to THAT
                self.gen.write_pop('pointer', 1)
                # retrieve the value, THAT 0
                self.gen.write_push('that', 0)
                return True
            elif self._expectExact('.', 'const', False):
                # If iden is a symbol, do sliding technique
                iden_sym = self.symbols.get(iden)
                if iden_sym is not None:
                    # We push the object as first argument
                    self.gen.write_push(
                        iden_sym['category'],
                        iden_sym['idx']
                    )
                # identifier.
                # subroutineName
                # TODO: ERROR HERE
                self._expectExact('identifier', 'type')
                func_name = self.cur_token['const']
                self._expectExact('(', 'const')
                n_args = self.compileExpressionList()
                self._expectExact(')', 'const')
                if iden_sym is not None:
                    # If symbol, add 1 to arg to include "this"
                    self.gen.write_call(
                        f"{iden_sym['type']}.{func_name}",
                        n_args+1
                    )
                else:
                    # Typical Class.sub call
                    self.gen.write_call(
                        f"{iden}.{func_name}",
                        n_args
                    )
            elif self._expectExact('(', 'const', False):
                # if only iden(), assume this is a method call
                # so we push the current pointer as an argument as well
                self.gen.write_push('pointer', 0)
                n_args = self.compileExpressionList()
                self.gen.write_call(f"{self.class_name}.{iden}", n_args+1)
                self._expectExact(')', 'const')
            else:
                symbol = self.symbols.get(iden)
                self.gen.write_push(
                    symbol['category'],
                    symbol['idx']
                )
                return True
        return False

    def compileOp(self, strict=True):
        return self._expectChoices(
            ['+', '-', '*', '/', '&amp;', '|', '&lt;', '&gt;', '='],
            [
                'const', 'const', 'const',
                'const', 'const', 'const',
                'const', 'const', 'const'
            ],
            strict
        )

    def compileLetStatement(self):
        is_arr = False
        self._expectExact('let', 'const')
        self._expectExact('identifier', 'type')
        symbol = self.symbols.get(self.cur_token['const'])
        if self._expectExact('[', 'const', False):
            is_arr = True
            # We push base address of arr
            self.gen.write_push(
                symbol['category'],
                symbol['idx']
            )
            self.compileExpression()
            # We then add base + exp to compute the dest addr
            self.gen.write_arith('+')
            self._expectExact(']', 'const')
        self._expectExact('=', 'const')
        self.compileExpression()
        self._expectExact(';', 'const')
        if not is_arr:
            self.gen.write_pop(symbol['category'], symbol['idx'])
        else:
            # save prev expression
            self.gen.write_pop('temp', 0)
            # get target dest addr
            self.gen.write_pop('pointer', 1)
            self.gen.write_push('temp', 0)
            self.gen.write_pop('that', 0)
    def compileIfStatement(self):
        true_lbl = f"IF_TRUE{self.flow_ctr['if']}"
        false_lbl = f"IF_FALSE{self.flow_ctr['if']}"
        self.flow_ctr['if'] += 1
        self._expectExact('if', 'const')
        self._expectExact('(', 'const')
        self.compileExpression()
        self.gen.write_arith('not')
        self._expectExact(')', 'const')
        self.gen.write_if_goto(true_lbl)
        self._expectExact('{', 'const')
        self.compileStatements()
        self._expectExact('}', 'const')
        self.gen.write_goto(false_lbl)
        self.gen.write_label(true_lbl)
        if self._expectExact('else', 'const', False):
            self._expectExact('{', 'const')
            self.compileStatements()
            self._expectExact('}', 'const')
        self.gen.write_label(false_lbl)

    def compileWhileStatement(self):
        start_lbl = f"WHILE_EXP{self.flow_ctr['while']}"
        end_lbl = f"WHILE_END{self.flow_ctr['while']}"
        self.flow_ctr['while'] += 1
        self._expectExact('while', 'const')
        self.gen.write_label(start_lbl)
        self._expectExact('(', 'const')
        self.compileExpression()
        self.gen.write_arith('not')
        self._expectExact(')', 'const')
        self.gen.write_if_goto(end_lbl)
        self._expectExact('{', 'const')
        self.compileStatements()
        self._expectExact('}', 'const')
        self.gen.write_goto(start_lbl)
        self.gen.write_label(end_lbl)

    def compileDoStatement(self):
        self._expectExact('do', 'const')
        self._expectExact('identifier', 'type')
        iden = self.cur_token['const']
        if self._expectExact('(', 'const', False):
            # if only iden(), assume this is a method call
            # so we push the current pointer as an argument as well
            self.gen.write_push('pointer', 0)
            n_args = self.compileExpressionList()
            self._expectExact(')', 'const')
            self.gen.write_call(f"{self.class_name}.{iden}", n_args+1)
        elif self._expectExact('.', 'const', False):
            iden_sym = self.symbols.get(iden)
            if iden_sym is not None:
                # We push the object as first argument
                self.gen.write_push(
                    iden_sym['category'],
                    iden_sym['idx']
                )
            self._expectExact('identifier', 'type')
            func_name = self.cur_token['const']
            self._expectExact('(', 'const')
            n_args = self.compileExpressionList()
            self._expectExact(')', 'const')
            if iden_sym is not None:
                self.gen.write_call(
                    f"{iden_sym['type']}.{func_name}",
                    n_args+1
                )
            else:
                self.gen.write_call(
                    f"{iden}.{func_name}",
                    n_args
                )
        self._expectExact(';', 'const')
        # Clean up after yourself bruh
        self.gen.write_pop('temp', 0)

    def compileReturnStatement(self):
        self._expectExact('return', 'const')
        if not self.compileExpression():
            # If no return value, assume it is void!
            self.gen.write_push('constant', 0)
        self._expectExact(';', 'const')
        self.gen.write_return()

    def compileStatements(self):
        statements = ['let', 'if', 'while', 'do', 'return']
        token = self.tokenizer.get_token()
        if token['const'] in statements:
            while token['const'] in statements:
                if token['const'] == 'let':
                    self.compileLetStatement()
                elif token['const'] == 'if':
                    self.compileIfStatement()
                elif token['const'] == 'while':
                    self.compileWhileStatement()
                elif token['const'] == 'do':
                    self.compileDoStatement()
                elif token['const'] == 'return':
                    self.compileReturnStatement()
                token = self.tokenizer.get_token()

    def compileVarDec(self):
        ctr = 0
        while self._expectExact('var', 'const', False, 'varDec'):
            ctr += 1
            self.compileType()
            typing = self.cur_token['const']
            self._expectExact('identifier', 'type')
            name = self.cur_token['const']
            self.symbols.set(name, typing, 'local')
            while self._expectExact(',', 'const', False):
                ctr += 1
                self._expectExact('identifier', 'type')
                name = self.cur_token['const']
                self.symbols.set(name, typing, 'local')
            self._expectExact(';', 'const')
        return ctr

    def compileSubroutineBody(self, routine_name, sub_metadata):
        self._expectExact('{', 'const')
        self.gen.write_function(
            f"{self.class_name}.{routine_name}",
            self.compileVarDec()
        )
        if sub_metadata['typing'] == 'constructor':
            self.gen.write_push('constant', sub_metadata['n_fields'])
            self.gen.write_call('Memory.alloc', 1)
            self.gen.write_pop('pointer', 0)
        elif sub_metadata['typing'] == 'method':
            # Set first argument to pointer 0 so we align ourselves
            self.gen.write_push('argument', 0)
            self.gen.write_pop('pointer', 0)
        self.compileStatements()
        self._expectExact('}', 'const')
        self.symbols.reset_subroutine()

    def compileType(self, strict=True):
        return self._expectChoices(
            ['int', 'char', 'boolean', 'identifier'],
            ['const', 'const', 'const', 'type'],
            strict=strict
        )

    def compileParameterList(self, sub_metadata):
        # type
        if not self.compileType(strict=False):
            return

        # if method, slide in "this" to arguments
        if sub_metadata['typing'] == 'method':
            self.symbols.set('this', 'this', 'argument')
        typing = self.cur_token['const']
        # varName
        self._expectExact('identifier', 'type')
        name = self.cur_token['const']
        self.symbols.set(name, typing, 'argument')
        while self._expectExact(',', 'const', False):
            self.compileType()
            typing = self.cur_token['const']
            self._expectExact('identifier', 'type')
            name = self.cur_token['const']
            self.symbols.set(name, typing, 'argument')

    def compileSubroutineDec(self, n_fields):
        # ('constructor' | 'function' | 'method')
        # Turn to subroutine metadata,
        sub_metadata = {
            'typing': 'function',
            'n_fields': n_fields
        }
        match = self._expectChoices(
            ['constructor', 'function', 'method'],
            ['const', 'const', 'const'],
            False,
            'subroutineDec'
        )
        if match:
            while match:
                sub_metadata['typing'] = self.cur_token['const']
                # ('void' | type)
                self._expectChoices(
                    ['void', 'int', 'char', 'boolean', 'identifier'],
                    ['const', 'const', 'const', 'const', 'type'],
                )
                sub_metadata['return_typing'] = self.cur_token['const']
                # subroutineName
                self._expectExact('identifier', 'type')
                name = self.cur_token['const']
                self._expectExact('(', 'const')
                # If method, bump params +1
                self.compileParameterList(sub_metadata)
                self._expectExact(')', 'const')
                self.compileSubroutineBody(name, sub_metadata)
                # ('constructor' | 'function' | 'method')
                sub_metadata['typing'] = 'function'
                is_constructor = False
                match = self._expectChoices(
                    ['constructor', 'function', 'method'],
                    ['const', 'const', 'const'],
                    False,
                    'subroutineDec'
                )

    def compileClassVarDec(self):
        ctr = 0
        while self._expectChoices(['static', 'field'], ['const', 'const'], False, 'classVarDec'):
            category = self.cur_token['const']
            if category == 'field':
                ctr += 1
                category = 'this'
            self.compileType()
            typing = self.cur_token['const']
            self._expectExact('identifier', 'type')
            name = self.cur_token['const']
            self.symbols.set(name, typing, category)
            while self._expectExact(',', 'const', False):
                if category == 'this':
                    ctr += 1
                self._expectExact('identifier', 'type')
                name = self.cur_token['const']
                self.symbols.set(name, typing, category)
            self._expectExact(';', 'const', False)
        return ctr

    def compileClass(self):
        self._expectExact('class', 'const')
        self._expectExact('identifier', 'type')
        self._expectExact('{', 'const')
        n_fields = self.compileClassVarDec()
        self.compileSubroutineDec(n_fields)
        self._expectExact('}', 'const')
        self.symbols.reset_class()
        self.gen.close_file()
