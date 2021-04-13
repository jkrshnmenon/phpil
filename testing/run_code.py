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
    runner = executor.Executor(PHP_BINARY, cmdline_flags=['-c', '/home/hacker/php.ini'], is_stdin=False)
    watchdog = coverage.Coverage(SANCOV_SCRIPT)

    with open(f'{sys.argv[1]}', 'r') as f:
        code = f.read().strip()
    runner.code = code
    runner.execute()
    for sancov_file in watchdog.find_reports('/tmp/coverages'):
        watchdog.analyze(obj=PHP_BINARY, report_file=sancov_file)
    watchdog.clear_reports('/tmp/coverages')
    runner.dump_inputs('/home/hacker/workspace/fuzzer_inputs.json')
    watchdog.dump_coverage('/home/hacker/workspace/coverage.json')


if __name__ == '__main__':
    main()
