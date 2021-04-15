import os
import sys
import json
import logging
import tempfile
from collections import defaultdict

import pwnlib

logger = logging.getLogger('Executor')
#logging.getLogger('pwnlib.tubes.process.process').setLevel(logging.DEBUG)

class Executor:
    '''
    This class takes care of executing the target binary with the inputs
    '''
    def __init__(self, binary, output_dir, cmdline_flags=None, code=None, is_stdin=False, extra_args=None):
        '''
        @param binary:          The path to the binary
        @param output_dir:      The directory to store the outputs and inputs in
        @param cmdline_flags:   The command line flags to the binary
        @param code:            The fuzzer generated program
                                Code can be none so that this object can be re-used for other inputs.
        @param is_stdin:        Whether the input is to be read via stdin or not
        @param extra_args:      Any args that might be required after the filename
        '''
        self._program_path = binary
        self._program_args = cmdline_flags
        self._output_dir = output_dir
        self._extra_args = [] if extra_args is None else extra_args
        self._is_stdin = is_stdin
        self._non_zero_exits = defaultdict(list)
        self.code = code
        self.crash_num = 0
    
    def execute(self, collect_stderr=False, save_input=False):
        logger.info("Executing %s" % self._program_path)
        assert collect_stderr is False, "Not Implemented!"
        assert self.code is not None, "There is no code to run!"
        if save_input is True:
            with open(f'{self._output_dir}/saved_input.php', 'w') as f:
                f.write(self.code)

        # handle stdin cases
        if self._is_stdin:
            logger.info("Running with stdin")
            return self._execute()

        # handle non stdin cases
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php') as fp:
            fp.write(self.code)
            fp.seek(0)
            fp.flush()
            logger.info("Running with payload in temporary file %s" % fp.name)
            return self._execute(filename=fp.name)
    
    def dump_inputs(self, filename='fuzzer_inputs.json'):
        with open(os.path.join(self._output_dir, filename), 'w') as f:
            json.dump(self._non_zero_exits, f, indent=2)

    def _execute(self, filename=None):
        output, err, exit_code = b'', b'', 255

        cmd = self._build_command(filename=filename)

        env = os.environ.copy()
        env["ASAN_OPTIONS"] = "coverage=1:coverage_dir=/tmp/coverages/"
        r = pwnlib.tubes.process.process(cmd, env=env)
        r.wait(timeout=5)
        exit_code = r.poll()
        if exit_code is None:
            r.kill()
            exit_code = 255
        output = r.recvall(timeout=1).strip().decode('utf-8')
        logger.info("Received %d bytes of output" % len(output))
        
        logger.info("Process exited with exit code %d", exit_code)
        # we only record weird exit_code
        # 0 means everything is fine
        # -1/255 means syntax error
        if exit_code not in {0, 255, -1}:
            logger.info("Logging code with exit_code: %d", exit_code)
            self._non_zero_exits[exit_code].append({'input': self.code, 'output': output})
            self.crash_num += 1

        return output, err, exit_code

    def _build_command(self, filename=None):
        if self._is_stdin:
            return [f'{self._program_path}'] + self._program_args + self._extra_args

        assert filename is not None, "File name is required when input is not from stdin"
        return [f'{self._program_path}'] + self._program_args + [f'{filename}'] + self._extra_args
        
