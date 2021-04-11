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
TARGET_SRC = "../../../targets/orig-php-src/"
TARGET = os.path.join(TARGET_SRC, "sapi/cli/php")
#CLANG_LIB_PATH = '/usr/local/lib/'
#CLANG_INCLUDE_PATH = '/usr/local/lib/clang/11.0.0/include'

# init
e = pwnlib.elf.ELF(TARGET)
parser_addr = e.symbols['zend_parse_parameters']
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
# 1. parse zend_function_entry ext_functions
# 2. intercept zend_parse_method_parameters for class functions

# reference: Zend/zend_API.c zend_parse_arg_impl
mapping = {
        "|": "Z_PARAM_OPTIONAL",
        "l": "Z_PARAM_LONG",
        "d": "Z_PARAM_DOUBLE",
        "n": "Z_PARAM_NUMBER",
        "s": "Z_PARAM_STRING",
        "p": "Z_PARAM_PATH", # must not contain any null bytes
        "P": "Z_PARAM_PATH", # TODO: difference between p and P?
        "S": "Z_PARAM_STRING", # TODO: difference between s and S?
        "b": "Z_PARAM_BOOL",
        "r": "Z_PARAM_RESOURCE",
        "a": "Z_PARAM_ARRAY",
        "A": "Z_PARAM_ARRAY", # a and A are the same
        "h": "Z_PARAM_ARRAY_HT",
        "H": "Z_PARAM_ARRAY_HT", # h and H are the same, ARRAY_HT is HashTable
        "o": "Z_PARAM_OBJECT",
        "O": "Z_PARAM_OBJECT_OF_CLASS",
        "C": "Z_PARAM_CLASS",
        "f": "Z_PARAM_FUNC",
        "z": "Z_PARAM_ZVAL",
        "Z": "deprecated",
        "L": "deprecated",
        "+": "Z_PARAM_VARIADIC(+)",
        "*": "Z_PARAM_VARIADIC(*)",
        }

def list_builtins():
    cmd = [TARGET, "-r", "echo json_encode(get_defined_functions());"]
    r = pwnlib.tubes.process.process(cmd)
    output = r.recvall()
    res = json.loads(output)
    assert 'internal' in res and res['internal']
    return res['internal']

# reference: Zend/zend_API.c zend_parse_va_args
def calc_arg_bound(fmt):
    min_num_args = 0
    max_num_args = 0
    have_optional = 0
    have_varargs = 0
    post_varargs = 0
    for f in fmt:
        if f in 'ldsbraoOzZChfAHpSPLn':
            max_num_args += 1
        elif f == '|':
            min_num_args = max_num_args
            have_optional = 1
        elif f in '+*':
            have_varargs = 1
            if f == '+':
                max_num_args += 1
            post_varargs = max_num_args
    if not have_optional:
        min_num_args = max_num_args
    if have_varargs:
        max_num_args = -1
    return (min_num_args, max_num_args)

def transform(fmt):
    ret = []
    # ignore is_null check, we feed null for every value
    fmt = fmt.replace("!", "")
    return [calc_arg_bound(fmt)] + [mapping[x] for x in fmt]

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
        fmt = re.search(b'\"(.*)\"', lastline).group(1).decode()
        return transform(fmt)

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
        res = re.search(r'\(([-+\d]+),([-+\d]+)\)', ''.join(macros[0]))
        min_num = int(res.group(1))
        max_num = int(res.group(2))

        # extract argument types
        args = [(min_num, max_num)]
        for macro in macros:
            if not macro[0].startswith("Z_PARAM"):
                continue

            op = macro[0]
            if op == "Z_PARAM_VARIADIC":
                op = "%s(%s)" % (macro[0], macro[2].strip("\'\""))
            args.append(op)
        return args

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
d = {}

for func in funcs:
    #if func != 'var_dump':
    #    continue
    print(f"func: {func}")
    raw_arg_type = extract_arg_type(func)
    print(f"arg_type: {raw_arg_type}")
    if raw_arg_type:
        d[func] = raw_arg_type
    #exit(0)

with open("result.json", "w") as f:
    f.write(json.dumps(d))
