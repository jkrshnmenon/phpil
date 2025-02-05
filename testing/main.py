import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PhpIL import program_builder
from PhpIL import program
from PhpIL import lifter
from PhpIL import executor
from PhpIL import coverage

logger = logging.getLogger('Executor')
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')


PHP_BINARY = '/home/hacker/targets/php-phpil-asan-src/sapi/cli/php'
SANCOV_SCRIPT = '/home/hacker/phpil/testing/sancov.py'

def main():
    runner = executor.Executor(PHP_BINARY, output_dir='/home/hacker/workspace', cmdline_flags=['-c', '/home/hacker/php.ini'], is_stdin=False)
    watchdog = coverage.Coverage(SANCOV_SCRIPT, output_dir='/home/hacker/workspace')
    while True:
        try:
            pb = program_builder.ProgramBuilder(init_builtins=True)
            for _ in range(4):
                pb.generateRandomInst()

            prog = pb.finish()

            lift = lifter.Lifter(prog)
            lift.doLifting()
            code = lift.getCode()
            # print(code)
            # Mutate code
            runner.code = code
            runner.execute(save_input=True)
            for sancov_file in watchdog.find_reports('/tmp/coverages'):
                watchdog.analyze(obj=PHP_BINARY, report_file=sancov_file)
            watchdog.clear_reports('/tmp/coverages')
        except:
            runner.dump_inputs('fuzzer_inputs.json')
            watchdog.dump_coverage('coverage.json')
            break


if __name__ == '__main__':
    main()
