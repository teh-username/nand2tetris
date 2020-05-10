class CodeGen:
    arith_lookup = {
        '+': 'add',
        '-': 'sub',
        '*': 'call Math.multiply 2',
        '/': 'call Math.divide 2',
        'neg': 'neg',
        'not': 'not',
        '&gt;': 'gt',
        '&lt;': 'lt',
        '&amp;': 'and',
        '|': 'or',
        '=': 'eq',
    }

    def __init__(self, outfile):
        self.outfile = open(outfile, 'w')

    def close_file(self):
        self.outfile.close()

    def _out(self, str):
        self.outfile.write(f"{str}\n")

    def write_push(self, segment, idx):
        self._out(f"push {segment} {idx}")

    def write_pop(self, segment, idx):
        self._out(f"pop {segment} {idx}")

    def write_arith(self, symbol):
        self._out(self.arith_lookup[symbol])

    def write_label(self, name):
        self._out(f"label {name}")
        pass

    def write_goto(self, name):
        self._out(f"goto {name}")

    def write_if_goto(self, name):
        self._out(f"if-goto {name}")

    def write_call(self, name, n_args):
        self._out(f"call {name} {n_args}")

    def write_return(self):
        self._out('return')

    def write_function(self, name, n_locals):
        self._out(f"function {name} {n_locals}")
