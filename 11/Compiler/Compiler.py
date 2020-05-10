import glob
import os
import sys

from SyntaxAnalyzer import CompilationEngine
from SymbolTable import SymbolTable
from CodeGen import CodeGen

def compile(tar):
    for name in glob.glob(f'{tar}/*.jack'):
        (path, filename) = name.rsplit('/', 1)
        file_no_ext = filename.split('.')[0]
        engine = CompilationEngine(
            path,
            file_no_ext,
            SymbolTable(),
            CodeGen(f"{path}/{file_no_ext}.vm")
        )

if __name__ == '__main__':
    path = sys.argv[1]
    tar = os.path.join(os.path.dirname(__file__), path)
    compile(tar)
