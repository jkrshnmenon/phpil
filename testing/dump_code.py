import os
import sys
import logging
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PhpIL import program_builder
from PhpIL import program
from PhpIL import lifter
from PhpIL import executor
from PhpIL import coverage

random.seed(1)

logger = logging.getLogger('Executor')
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')


PHP_BINARY = '/home/hacker/targets/php-phpil-asan-src/sapi/cli/php'
SANCOV_SCRIPT = '/home/hacker/phpil/testing/sancov.py'

def main():
    from PhpIL import instructions
    from PhpIL import operation
    from PhpIL import typesData
    from PhpIL import variable
    from PhpIL import analyzer
    # prog = program.Program([
    #     instructions.Instruction(operation.LoadString("somestring"),False,[variable.Variable(3)]),
    #     # instructions.Instruction(operation.BuiltinFunction(typesData.FunctionSignature(1,[])),False,[variable.Variable('var_dump')],[]),
    #     # instructions.Instruction(operation.BeginFunction(typesData.FunctionSignature(2,[variable.Variable(11)])),False,[variable.Variable(1)],[variable.Variable(10),variable.Variable(11)]),
    #     # instructions.Instruction(operation.Return(),[variable.Variable(2)]),
    #     # instructions.Instruction(operation.EndFunction()),
    #     # instructions.Instruction(operation.CallFunction(2),[variable.Variable(1), variable.Variable(4), variable.Variable(0)],[variable.Variable(6)]),
    #     instructions.Instruction(operation.CallFunction(1),[variable.Variable('var_dump'), variable.Variable(3)],[variable.Variable(7)]),
    #     # instructions.Instruction(operation.BinaryOperation("+"),[variable.Variable(10),variable.Variable(11)],[variable.Variable(2)]),
    #     # instructions.Instruction(operation.LoadString("somestring"),False,[variable.Variable(3)]),
    #     # instructions.Instruction(operation.LoadInteger(1337),False,[variable.Variable(4)]),
    # ])
    # print(prog)
    # pb = program_builder.ProgramBuilder(prog, init_builtins=True)
    runner = executor.Executor(PHP_BINARY, output_dir="/tmp", cmdline_flags=['-c', '/home/hacker/php.ini'], is_stdin=False)
    watchdog = coverage.Coverage(SANCOV_SCRIPT)
    pb = program_builder.ProgramBuilder(init_builtins=True)
    
    for _ in range(4):
        pb.generateRandomInst()

    prog = pb.finish()

    lift = lifter.Lifter(prog)
    lift.doLifting()
    code = lift.getCode()
    runner.code = code
    runner.execute()
    for sancov_file in watchdog.find_reports('/tmp/coverages'):
        watchdog.analyze(obj=PHP_BINARY, report_file=sancov_file)
    watchdog.clear_reports('/tmp/coverages')
    print(code)
    #runner.dump_inputs('/home/hacker/workspace/fuzzer_inputs.json')
    #watchdog.dump_coverage('/home/hacker/workspace/coverage.json')


if __name__ == '__main__':
    main()
