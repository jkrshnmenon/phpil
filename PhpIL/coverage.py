import os
import sys
import json
import logging
import subprocess
import pwn

logger = logging.getLogger('Coverage')

class Coverage:
    '''
    '''
    def __init__(self, sancov_script, report_path=None, output_dir=None):
        self._script_path = sancov_script
        self._report_path = report_path
        self._output_dir = output_dir
        self._hash_map = {}
    
    def _make_hash(self, e1, e2):
        return f'{hex(e1)}-{hex(e2)}'
    
    def _mark_edge_uncovered(self, key):
        self._hash_map[key] = True
    
    def _edge_is_uncovered(self, key):
        return key in self._hash_map and self._hash_map[key] is True
    
    @property
    def report_path(self):
        return self._report_path
    
    @report_path.setter
    def report_path(self, new_path):
        self._report_path = new_path
    
    def dump_coverage(self, filename='coverage.json'):
        if len(self._hash_map) == 0:
            logger.info("No coverages to dump")
            return
        
        with open(f'{self._output_dir}/{filename}', 'w') as f:
            json.dump(self._hash_map, f, indent=2)

    def find_reports(self, report_dir):
        report_paths = []
        logger.debug("Looking for sancov files in %s" % report_dir)

        for report_file in os.listdir(report_dir):
            if not report_file.endswith('.sancov'):
                logger.debug("Discarding %s since it doesn't end with .sancov" % report_file)
                continue
            report_paths.append(os.path.abspath(os.path.join(report_dir, report_file)))
        
        logger.debug("Found %d sancov files in %s" % (len(report_paths), report_dir))
        return report_paths
    
    def clear_reports(self, report_dir):
        for report_file in os.listdir(report_dir):
            if not report_file.endswith('.sancov'):
                continue
            logger.debug("Removing sancov report %s" % report_file)
            os.remove(os.path.abspath(os.path.join(report_dir, report_file)))
    
    def analyze(self, dump_source=False, obj=None, report_file=None):
        if self._report_path is None:
            assert report_file is not None, "Sancov file not specified"
            self._report_path = report_file
        elif report_file is not None:
            self._report_path = report_file

        err = ''
        logger.info("Using pwn module")
        output = pwnlib.tubes.process.process([f'{self._script_path}', 'print', f'{self._report_path}'], stderr=subprocess.PIPE).recvall().strip().decode('utf-8')
        
        if not dump_source:
            pc_addrs = list(map(lambda x: int(x, 16), output.splitlines()))
            logger.info("Found %d PC values" % len(pc_addrs))
            logger.info("Marking edges in hash map")
            old_edges = len(self._hash_map)
            for idx in range(len(pc_addrs)-1):
                key = self._make_hash(pc_addrs[idx], pc_addrs[idx+1])
                self._mark_edge_uncovered(key)
            new_edges = len(self._hash_map)
            logger.info("Found %d new edges" % (new_edges-old_edges))
            return pc_addrs
        
        return set(list(self._pc_addrs_to_source(output.splitlines(), obj).values()))

    def _pc_addrs_to_source(self, pc_addrs, obj):
        assert obj is not None, "Binary object is required to dump source code"
        if isinstance(obj, list):
            binary_objects = obj
        else:
            binary_objects = [obj]

        idx = 0
        pc_source_map = {}
        missing_pcs = set(pc_addrs) - set(list(pc_source_map.keys())) 

        while len(missing_pcs) > 0 and idx < len(binary_objects):
            obj = binary_objects[idx]
            logger.debug("Using %s as binary object" % obj)
            for pc in missing_pcs:
                retval = self._pc_to_source(pc, obj)
                if retval is None:
                    continue
                pc_source_map[pc] = retval
            missing_pcs = set(pc_addrs) - set(list(pc_source_map.keys())) 
            idx += 1
        
        if len(missing_pcs) > 0:
            logger.info("Could not find source mappings for %d PC values" % len(missing_pcs))
        
        return pc_source_map
    
    def _pc_to_source(self, pc_addr, obj):
        line = pwnlib.tubes.process.process(['llvm-symbolizer', '--obj', f'{obj}', pc]).recvall().strip().decode('utf-8').splitlines()
        for idx in range(0, len(line), 2):
            func_name = line[idx]
            filename, line_num, _ = line[idx+1].split(':')

        if filename == '??':
            return None

        logger.debug("Function %s in file %s @ %s" % (func_name, filename, line_num))
        return {'function': func_name, 'filename': filename, 'line': line_num}
