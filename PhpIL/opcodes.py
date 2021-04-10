class opcodes:

    opcodeList = [ "Nop", "LoadInteger", "LoadFloat", "LoadString", "LoadBoolean", "LoadNull", "CreateObject", "CreateArray", "CallFunction", "Print", "BeginFunction", "EndFunction", "BeginIf", "BeginElse", "EndIf", "BeginWhile", "EndWhile", "BeginFor", "EndFor", "BeginForEach", "EndForEach", "Return", "Break", "Continue", "BeginTry", "BeginCatch", "EndTryCatch", "BeginClass", "EndClass", "UnaryOperation", "BinaryOperation", "Include", "Eval", "Phi", "Copy", "BeginDoWhile", "EndDoWhile", "ThrowException","CreateDict","GetArrayElem","BuiltinMethod","BuiltinMethod"]

    Nop, \
    LoadInteger, \
    LoadFloat, \
    LoadString, \
    LoadBoolean, \
    LoadNull, \
    CreateObject, \
    CreateArray, \
    CallFunction, \
    Print, \
    BeginFunction, \
    EndFunction, \
    BeginIf, \
    BeginElse, \
    EndIf, \
    BeginWhile, \
    EndWhile, \
    BeginFor, \
    EndFor, \
    BeginForEach, \
    EndForEach, \
    Return, \
    Break, \
    Continue, \
    BeginTry, \
    BeginCatch, \
    EndTryCatch, \
    BeginClass, \
    EndClass, \
    UnaryOperation, \
    BinaryOperation, \
    Include, \
    Eval, \
    Phi, \
    Copy, \
    BeginDoWhile, \
    EndDoWhile, \
    ThrowException, \
    CreateDict, \
    GetArrayElem, \
    BuiltinMethod, \
    SetArrayElem = range(len(opcodeList))



if __name__ == '__main__':
    print(opcodes.Nop)
