class Variable:

    def __init__(self, id):
        self.id = id
        self._repr = None

    def set_repr(self, repr):
        self._repr = repr

    def __eq__(self, other):
        if not isinstance(other, Variable):
            return False
        return self.id == other.id

    def __str__(self):
        if self._repr is None:
            return "$v"+str(self.id)
        return self._repr

    def __hash__(self):
        return self.id

    def __repr__(self):
        return self.__str__()

if __name__ == '__main__':
    print (Variable(1))
