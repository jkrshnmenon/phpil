class Variable:

    def __init__(self,id):
        self.id = id

    def __eq__(self, other):
        if not isinstance(other, Variable):
            return False
        if self.id == other.id:
            return True
        return False

    def __str__(self):
        if isinstance(self.id, int):
            retval = "$v"+str(self.id)
        else:
            retval = "$" + self.id
        return retval

    def __hash__(self):
        # print "AA"
        return hash(self.id)

    def __repr__(self):
        if isinstance(self.id, int):
            retval = "v"+str(self.id)
        else:
            retval = self.id
        return retval

if __name__ == '__main__':
    print (Variable(1))
