import glob
import os
import re
import sys

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
        self.p = re.compile(r"(?:\/\*\*[\S\s]*?\*\/)|(?:\/\/.*$)|(class|constructor|function|method|field|static|var|int|char|boolean|void|true|false|null|this|let|do|if|else|while|return)|(\{|\}|\(|\)|\[|\]|\.|\,|\;|\+|\-|\*|\/|\&|\||\<|\>|\=|\~)|((?<=\").*(?=\"))|((?:[_a-zA-Z]+)(?:[_a-zA-Z0-9]?))|([0-9]+)", re.MULTILINE)
        self.tokens = []
        with open(filename, 'r') as infile:
            self._tokenize_file(infile.read())

    def get_token(self):
        return self.tokens[0]

    def advance(self):
        self.tokens = self.tokens[1:]

    def has_tokens(self):
        return len(self.tokens)

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

    def output_as_xml(self, filename, path):
        with open(f"{path}/_{filename}T.xml", 'w') as outfile:
            outfile.write('<tokens>\n')
            while self.has_tokens():
                tok = self.get_token()
                outfile.write(f"<{tok['type']}> {tok['const']} </{tok['type']}>\n")
            outfile.write('</tokens>\n')

class CompilationEngine:
    def __init__(self, path, filename):
        self.tokenizer = Tokenizer(f"{path}/{filename}.jack")
        self.outfile = open(f"{path}/_{filename}.xml", 'w')
        self.inject_expression_open_tag = False
        self.inject_expression_close_tag = False
        self.compileClass()

    def _expectExact(self, expected, attr, strict=True, parentTag=None):
        token = self.tokenizer.get_token()
        if token[attr] != expected:
            if strict:
                raise Exception(f"Expected {expected}, got {token[attr]}")
            return False
        self.printToken(token, parentTag)
        return True

    def _expectChoices(self, expected, attr, strict=True, parentTag=None):
        token = self.tokenizer.get_token()
        for idx, expect in enumerate(expected):
            if token[attr[idx]] == expect:
                self.printToken(token, parentTag)
                return True
        if strict:
            raise Exception(f"Expected either {expected}, got {token}")
        return False

    def printToken(self, token, parentTag=None):
        if self.inject_expression_open_tag:
            self.outfile.write("<expression>\n")
            self.inject_expression_open_tag = False
            self.inject_expression_close_tag = True
        if parentTag:
            self.outfile.write(f"<{parentTag}>\n")
        self.outfile.write(f"<{token['type']}> {token['const']} </{token['type']}>\n")
        self.tokenizer.advance()

    def printRuleTag(self, name, closing=False):
        if closing:
            self.outfile.write(f"</{name}>\n")
        else:
            self.outfile.write(f"<{name}>\n")

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
        self.printRuleTag('expressionList')
        if not self.compileExpression():
            self.printRuleTag('expressionList', True)
            return
        while self._expectExact(',', 'const', False):
            self.compileExpression()
        self.printRuleTag('expressionList', True)

    def compileExpression(self):
        self.inject_expression_open_tag = True
        if not self.compileTerm():
            if self.inject_expression_open_tag:
                self.inject_expression_open_tag = False
            elif self.inject_expression_close_tag:
                self.printRuleTag('expression', True)
                self.inject_expression_close_tag = False
            return False
        while self.compileOp(False):
            self.inject_expression_close_tag = False
            self.compileTerm()
        self.printRuleTag('expression', True)
        return True

    def compileTerm(self):
        if self._expectExact('(', 'const', False, 'term'):
            self.compileExpression()
            self._expectExact(')', 'const')
            self.printRuleTag('term', True)
            return True
        if self.compileKeywordConstants(False, 'term'):
            self.printRuleTag('term', True)
            return True
        if self._expectExact('stringConstant', 'type', False, 'term'):
            self.printRuleTag('term', True)
            return True
        if self._expectExact('integerConstant', 'type', False, 'term'):
            self.printRuleTag('term', True)
            return True
        if self.compileUnaryOp(False, 'term'):
            self.compileTerm()
            self.printRuleTag('term', True)
            return True
        # If we're here, lookahead to determine which is which
        # varName
        if self._expectExact('identifier', 'type', False, 'term'):
            if self._expectExact('[', 'const', False):
                # identifier[]
                self.compileExpression()
                self._expectExact(']', 'const')
                self.printRuleTag('term', True)
                return True
            elif self._expectExact('.', 'const', False):
                # identifier.
                # subroutineName
                self._expectExact('identifier', 'type')
                self._expectExact('(', 'const')
                self.compileExpressionList()
                self._expectExact(')', 'const')
                self.printRuleTag('term', True)
            elif self._expectExact('(', 'const', False):
                # identifier()
                self.compileExpressionList()
                self._expectExact(')', 'const')
                self.printRuleTag('term', True)
            else:
                self.printRuleTag('term', True)
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
        self.printRuleTag('letStatement')
        self._expectExact('let', 'const')
        self._expectExact('identifier', 'type')
        if self._expectExact('[', 'const', False):
            self.compileExpression()
            self._expectExact(']', 'const')
        self._expectExact('=', 'const')
        self.compileExpression()
        self._expectExact(';', 'const')
        self.printRuleTag('letStatement', True)

    def compileIfStatement(self):
        self.printRuleTag('ifStatement')
        self._expectExact('if', 'const')
        self._expectExact('(', 'const')
        self.compileExpression()
        self._expectExact(')', 'const')
        self._expectExact('{', 'const')
        self.compileStatements()
        self._expectExact('}', 'const')
        if self._expectExact('else', 'const', False):
            self._expectExact('{', 'const')
            self.compileStatements()
            self._expectExact('}', 'const')
        self.printRuleTag('ifStatement', True)

    def compileWhileStatement(self):
        self.printRuleTag('whileStatement')
        self._expectExact('while', 'const')
        self._expectExact('(', 'const')
        self.compileExpression()
        self._expectExact(')', 'const')
        self._expectExact('{', 'const')
        self.compileStatements()
        self._expectExact('}', 'const')
        self.printRuleTag('whileStatement', True)

    def compileDoStatement(self):
        self.printRuleTag('doStatement')
        self._expectExact('do', 'const')
        self._expectExact('identifier', 'type')
        if self._expectExact('(', 'const', False):
            self.compileExpressionList()
            self._expectExact(')', 'const')
        elif self._expectExact('.', 'const', False):
            self._expectExact('identifier', 'type')
            self._expectExact('(', 'const')
            self.compileExpressionList()
            self._expectExact(')', 'const')
        self._expectExact(';', 'const')
        self.printRuleTag('doStatement', True)

    def compileReturnStatement(self):
        self.printRuleTag('returnStatement')
        self._expectExact('return', 'const')
        self.compileExpression()
        self._expectExact(';', 'const')
        self.printRuleTag('returnStatement', True)

    def compileStatements(self):
        statements = ['let', 'if', 'while', 'do', 'return']
        token = self.tokenizer.get_token()
        if token['const'] in statements:
            self.printRuleTag('statements')
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
            self.printRuleTag('statements', True)

    def compileVarDec(self):
        while self._expectExact('var', 'const', False, 'varDec'):
            self.compileType()
            self._expectExact('identifier', 'type')
            while self._expectExact(',', 'const', False):
                self._expectExact('identifier', 'type')
            self._expectExact(';', 'const')
            self.printRuleTag('varDec', True)

    def compileSubroutineBody(self):
        self.printRuleTag('subroutineBody')
        self._expectExact('{', 'const')
        self.compileVarDec()
        self.compileStatements()
        self._expectExact('}', 'const')
        self.printRuleTag('subroutineBody', True)

    def compileType(self, strict=True):
        return self._expectChoices(
            ['int', 'char', 'boolean', 'identifier'],
            ['const', 'const', 'const', 'type'],
            strict=strict
        )

    def compileParameterList(self):
        self.printRuleTag('parameterList')
        # type
        if not self.compileType(strict=False):
            self.printRuleTag('parameterList', True)
            return
        # varName
        self._expectExact('identifier', 'type')
        while self._expectExact(',', 'const', False):
            self.compileType()
            self._expectExact('identifier', 'type')
        self.printRuleTag('parameterList', True)

    def compileSubroutineDec(self):
        # ('constructor' | 'function' | 'method')
        match = self._expectChoices(
            ['constructor', 'function', 'method'],
            ['const', 'const', 'const'],
            False,
            'subroutineDec'
        )
        if match:
            while match:
                # ('void' | type)
                self._expectChoices(
                    ['void', 'int', 'char', 'boolean', 'identifier'],
                    ['const', 'const', 'const', 'const', 'type'],
                )
                # subroutineName
                self._expectExact('identifier', 'type')
                self._expectExact('(', 'const')
                self.compileParameterList()
                self._expectExact(')', 'const')
                self.compileSubroutineBody()
                self.printRuleTag('subroutineDec', True)
                # ('constructor' | 'function' | 'method')
                match = self._expectChoices(
                    ['constructor', 'function', 'method'],
                    ['const', 'const', 'const'],
                    False,
                    'subroutineDec'
                )

    def compileClassVarDec(self):
        while self._expectChoices(['static', 'field'], ['const', 'const'], False, 'classVarDec'):
            ran = True
            self.compileType()
            self._expectExact('identifier', 'type')
            while self._expectExact(',', 'const', False):
                self._expectExact('identifier', 'type')
            self._expectExact(';', 'const', False)
            self.printRuleTag('classVarDec', True)

    def compileClass(self):
        self.printRuleTag('class')
        self._expectExact('class', 'const')
        self._expectExact('identifier', 'type')
        self._expectExact('{', 'const')
        self.compileClassVarDec()
        self.compileSubroutineDec()
        self._expectExact('}', 'const')
        self.printRuleTag('class', True)
        self.outfile.close()

def _test_generate_tokens(tar):
    for name in glob.glob(f'{tar}/*.jack'):
        tk = Tokenizer(name)
        (path, filename) = name.split('/')
        tk.output_as_xml(filename.split('.')[0], path)

def compile(tar):
    for name in glob.glob(f'{tar}/*.jack'):
        (path, filename) = name.split('/')
        engine = CompilationEngine(path, filename.split('.')[0])

if __name__ == '__main__':
    path = sys.argv[1]
    tar = os.path.join(os.path.dirname(__file__), path)
    compile(tar)
