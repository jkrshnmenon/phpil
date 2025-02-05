import os
import sys
import time
import logging

import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PhpIL import program_builder
from PhpIL import program
from PhpIL import lifter
from PhpIL import executor
from PhpIL import coverage

logger = logging.getLogger('Executor')
logging.basicConfig(level=logging.ERROR, format='%(name)s - %(levelname)s - %(message)s')


PHP_BINARY = '/home/hacker/targets/php-phpil-asan-src/sapi/cli/php'
SANCOV_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sancov.py")
COVERAGE_DIR = "/tmp/coverages"

class Fuzzer:
    def __init__(self, binary, args):
        self.binary = binary
        self.args = args
        self.runner = executor.Executor(self.binary, cmdline_flags=args, is_stdin=False, output_dir='/home/hacker/workspace')
        self.watchdog = coverage.Coverage(SANCOV_SCRIPT, output_dir='/home/hacker/workspace')
        self.start_time = time.time()

        os.system(f"mkdir -p {COVERAGE_DIR}")

    def generate_input(self):
        pb = program_builder.ProgramBuilder(init_builtins=True)
        for _ in range(4):
            pb.generateRandomInst()

        prog = pb.finish()

        lift = lifter.Lifter(prog)
        lift.doLifting()
        code = lift.getCode()
        return code

    def collect_feedback(self):
        for sancov_file in self.watchdog.find_reports(COVERAGE_DIR):
            self.watchdog.analyze(obj=self.binary, report_file=sancov_file)
        self.watchdog.clear_reports(COVERAGE_DIR)

    def run_once(self):
        """
        finish one fuzzing iteration
        """
        # Mutate code
        code = self.generate_input()
        self.runner.code = code
        output, err, exit_code = self.runner.execute()
        print(f"exit_code: {exit_code}")
        self.collect_feedback()

    def run(self):
        pbar = tqdm.tqdm(bar_format="\rexec speed: {rate}\n")
        while True:
            try:
                print(f"crash_num: {self.runner.crash_num}")
                pbar.update(1)
                self.run_once()
            except KeyboardInterrupt:
                print("saving input and coverage...")
                self.runner.dump_inputs(filename='fuzzer_inputs.json')
                self.watchdog.dump_coverage('coverage.json')
                time.sleep(1)
            except Exception as e:
                logger.exception(e)

def main():
    fuzzer = Fuzzer(PHP_BINARY, ['-c', '/home/hacker/php.ini'])
    fuzzer.run()

if __name__ == '__main__':
    main()
