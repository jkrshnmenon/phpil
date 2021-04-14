import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PhpIL import program_builder
from PhpIL import program
from PhpIL import lifter
from PhpIL import executor
from PhpIL import coverage

#logger = logging.getLogger('Executor')
#logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

PHP_BINARY = '/home/hacker/targets/php-phpil-asan-src/sapi/cli/php'
SANCOV_SCRIPT = '/home/hacker/phpil/testing/sancov.py'

def main():
    from PhpIL import instructions
    from PhpIL import operation
    from PhpIL import typesData
    from PhpIL import variable
    from PhpIL import analyzer

    #pb = program_builder.ProgramBuilder()
    #pb.loadNull()
    #pb.loadString('x')
    #pb.beginFunction(typesData.FunctionSignature(2, []))
    #pb.loadInteger(8)
    #pb.doReturn([variable.Variable(2)])
    #pb.endFunction()
    #prog = pb.finish()

    prog = program.Program([
        instructions.Instruction(operation.LoadNull(), False, [variable.Variable(0)]),
        instructions.Instruction(operation.LoadString('x'), False, [variable.Variable(1)]),
        instructions.Instruction(operation.BeginFunction(typesData.FunctionSignature(2, [])),False, [variable.Variable(2)],[variable.Variable(3),variable.Variable(4)]),
        instructions.Instruction(operation.LoadInteger(8), False, [variable.Variable(5)]),
        instructions.Instruction(operation.CallFunction(2),[variable.Variable('str_repeat'), variable.Variable(4), variable.Variable(5)],[variable.Variable(6)]),
        instructions.Instruction(operation.BinaryOperation("."),[variable.Variable(3), variable.Variable(6)],[variable.Variable(7)]),
        instructions.Instruction(operation.CallFunction(1),[variable.Variable('var_dump'), variable.Variable(7)],[variable.Variable(8)]),
        instructions.Instruction(operation.EndFunction()),
        instructions.Instruction(operation.CallFunction(2),[variable.Variable(2), variable.Variable(0), variable.Variable(1)],[variable.Variable(6)]),
    ])
    print(prog)

    lift = lifter.Lifter(prog)
    lift.doLifting()
    code = lift.getCode()

    print(code)

if __name__ == '__main__':
    main()
