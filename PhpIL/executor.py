import os
import sys
import json
import logging
import tempfile
try:
    import pwn
except ImportError:
    import subprocess

logger = logging.getLogger('Executor')
logging.getLogger('pwnlib.tubes.process.process').setLevel(logging.ERROR)



class Executor:
    '''
    This class takes care of executing the target binary with the inputs
    '''
    def __init__(self, binary, cmdline_flags=None, code=None, is_stdin=False, extra_args=None):
        '''
        @param binary:          The path to the binary
        @param cmdline_flags:   The command line flags to the binary
        @param code:            The fuzzer generated program
                                Code can be none so that this object can be re-used for other inputs.
        @param is_stdin:        Whether the input is to be read via stdin or not
        @param extra_args:      Any args that might be required after the filename
        '''
        self._program_path = binary
        self._program_args = cmdline_flags
        self._extra_args = [] if extra_args is None else extra_args
        self._is_stdin = is_stdin
        self._code = code
        self._non_zero_exits = {}
    
    @property
    def code(self):
        return self._code
    
    @code.setter
    def code(self, code_obj):
        self._code = code_obj
    
    def execute(self, collect_stderr=False):
        logger.info("Executing %s" % self._program_path)
        assert collect_stderr is False, "Not Implemented!"
        assert self._code is not None, "There is no code to run!"
        if self._is_stdin:
            logger.info("Running with stdin")
            return self._run_with_input()
        else:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.php') as fp:
                fp.write(self._code)
                fp.seek(0)
                fp.flush()
                logger.info("Running with payload in temporary file %s" % fp.name)
                return self._run_with_temp_file(fp.name)
    
    def dump_inputs(self, filename='fuzzer_inputs.json'):
        if len(self._non_zero_exits) == 0:
            logger.info("No interesting inputs yet")
            return
        
        with open(filename, 'w') as f:
            json.dump(self._non_zero_exits, f, indent=2)
    
    def _run_with_input(self):
        command = ['ASAN_OPTIONS="coverage=1:coverage_dir=/tmp/coverages/"'] + self._build_command(stdin=True)
        output, err = '', ''
        if 'pwn' in sys.modules:
            process = pwn.process(' '.join(x for x in command), shell=True)
            process.sendline(self.code)
            output = process.recvall().strip().decode('utf-8')
        else:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            output, err = process.communicate(self.code)
            output = output.strip().decode('utf-8')
            err = err.strip().decode('utf-8')
        
        return output, err
    
    def _run_with_temp_file(self, filename):
        command = ['ASAN_OPTIONS="coverage=1:coverage_dir=/tmp/coverages/"'] + self._build_command(stdin=False, file_name=filename)
        output, err = '', ''
        if 'pwn' in sys.modules:
            logger.info("Using pwn module")
            process = pwn.process(' '.join(x for x in command), shell=True, alarm=5)
            output = process.recvall().strip().decode('utf-8')
            exit_code = process.poll()
            logger.info("Received %d bytes of output" % len(output))
        else:
            logger.info("Using subprocess module")
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
            output, err = process.communicate()
            output = output.strip().decode('utf-8')
            exit_code = process.returncode
            logger.info("Received %d bytes of output" % len(output))
            err = err.strip().decode('utf-8')
        
        logger.info("Process exited with exit code %d" % exit_code)
        if exit_code != 0:
            logger.info("Logging code")
            if exit_code not in self._non_zero_exits:
                self._non_zero_exits[exit_code] = []
            self._non_zero_exits[exit_code].append({'input': self._code, 'output': output})

        return output, err

    def _build_command(self, stdin=True, file_name=None):
        if stdin is False:
            assert file_name is not None, "File name is required when input is not from stdin"
            return [f'{self._program_path}'] + self._program_args + [f'{file_name}'] + self._extra_args
        else:
            return [f'{self._program_path}'] + self._program_args + self._extra_args
        
