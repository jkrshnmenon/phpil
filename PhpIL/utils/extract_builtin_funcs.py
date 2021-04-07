import os
import re
import json
import tempfile
import subprocess

import clang
import clang.cindex
#from clang.cindex import TokenKind, CursorKind
import pwnlib

# config
TARGET_SRC = "./targets/orig-php-src/"
TARGET = os.path.join(TARGET_SRC, "sapi/cli/php")
#CLANG_LIB_PATH = '/usr/local/lib/'
#CLANG_INCLUDE_PATH = '/usr/local/lib/clang/11.0.0/include'

# init
e = pwnlib.elf.ELF(TARGET)
parser_addr = e.symbols['zend_parse_parameters']
print(hex(parser_addr))
script_template = """ 
gef config context.enable 0
b *%#x
commands
x/s $rsi
end
r -r "%s();"
quit
"""
cidx = clang.cindex.Index.create()

# TODO:
# intercept zend_parse_method_parameters for class functions

def list_builtins():
    cmd = [TARGET, "-r", "echo json_encode(get_defined_functions());"]
    r = pwnlib.tubes.process.process(cmd)
    output = r.recvall()
    res = json.loads(output)
    assert 'internal' in res and res['internal']
    return res['internal']

def extract_arg_type_gdb(func):
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        script = script_template % (parser_addr, func)
        fp.write(script)
        fp.flush()
        r = pwnlib.tubes.process.process(["gdb", "-x", fp.name, TARGET])
        output = r.recvall().strip()
        lastline = output.splitlines()[-1]
        if b'exited' in lastline:
            return None
        print(lastline.decode())
        assert b':\t' in lastline
        return re.search(b'\"(.*)\"', lastline).group(1).decode()

def get_func_tokens(tu, func):
    raw_tokens = list(tu.get_tokens(extent=tu.cursor.extent))
    in_func = False
    tokens = []
    depth = 0
    for idx, token in enumerate(raw_tokens):
        if token.spelling == 'PHP_FUNCTION' and raw_tokens[idx+2].spelling == func:
            in_func = True
        if in_func:
            tokens.append(token)
            if token.spelling == '{':
                depth += 1
            if token.spelling == '}':
                depth -= 1

            if token.spelling == '}' and depth == 0:
                return tokens
    return None

def get_parse_tokens(func_tokens):
    flag = False
    tokens = []
    for idx, token in enumerate(func_tokens):
        if token.spelling == 'ZEND_PARSE_PARAMETERS_START':
            flag = True
        if token.spelling == 'ZEND_PARSE_PARAMETERS_NONE' or token.spelling == 'zend_parse_parameters_none':
            return None
        if token.spelling == 'ZEND_PARSE_PARAMETERS_END':
            tokens.append(token.spelling)
            break
        if flag:
            tokens.append(token.spelling)
    if not tokens:
        raise ValueError("can't find parsing macros!")
    tokens += ['(', ')']
    return tokens

def extract_arg_type_libclang(func):
    output  = subprocess.getoutput(f"grep -r PHP_FUNCTION\({func}\) {TARGET_SRC}")
    if "PHP_FUNCTION" not in output:
        return None
    path = output.split(":")[0]
    tokens = None
    try:
        tu = cidx.parse(path, options=0x200)

        # find the function first
        func_tokens = get_func_tokens(tu, func)

        tokens = get_parse_tokens(func_tokens)
        # handle special case where the function does not take arguments
        if not tokens:
            return []

        # parse macros
        last_idx = 0
        macros = []
        for idx, token in enumerate(tokens):
            if (token.startswith("ZEND_") or token.startswith("Z_PARAM")) and last_idx != idx:
                macros.append(tokens[last_idx:idx])
                last_idx = idx
        macros.append(tokens[last_idx:])

        # parse argument number
        res = re.search(r'\((\d+),(\d+)\)', ''.join(macros[0]))
        print(res.group(1))
        print(res.group(2))
        min_num = int(macros[0][2])
        max_num = int(macros[0][4])

        if min_num == max_num:
            print("handle")
            print(macros[min_num][0])
        else:
            raise NotImplementedError("we only handle min_num == max_num at this moment")

        print(macros)
        print(min_num, max_num)
        print('-'*0x10)

    except Exception as e:
        print("error", e)
        if tokens:
            print(tokens)
        return None

def extract_arg_type(func):

    res = extract_arg_type_gdb(func)
    if res is not None:
        return res

    res = extract_arg_type_libclang(func)
    if res is not None:
        return res

    return None

funcs = list_builtins()

for func in funcs:
    #if func != 'str_repeat':
    #    continue
    print(f"func: {func}")
    raw_arg_type = extract_arg_type(func)
    print(f"arg_type: {raw_arg_type}")
    #exit(0)
