class SymbolTable:
    def __init__(self):
        self.c_table = {}
        self.ctr = {
            'this': 0,
            'static': 0,
            'local': 0,
            'argument': 0,
        }
        self.s_table = {}
        self.table = {
            'this': self.c_table,
            'static': self.c_table,
            'local': self.s_table,
            'argument': self.s_table,
        }

    def set(self, name, typing, category):
        self.table[category][name] = {
            'category': category,
            'type': typing,
            'idx': self.ctr[category]
        }
        self.ctr[category] += 1

    def get(self, name):
        if name in self.s_table:
            return self.s_table[name]
        elif name in self.c_table:
            return self.c_table[name]
        return None

    def reset_class(self):
        self.c_table.clear()
        self.ctr['field'] = 0
        self.ctr['static'] = 0

    def reset_subroutine(self):
        self.s_table.clear()
        self.ctr['local'] = 0
        self.ctr['argument'] = 0

    def in_table(self, name):
        return False if self.get(name) is None else True

    def print(self):
        print("="*30)
        print(self.c_table)
        print(self.s_table)
        print("="*30)
