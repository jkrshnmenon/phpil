from . import program
from . import codeEmitter
from . import instructions
from . import probability
from . import operation
from . import variable
from . import typesData
from .opcode import Opcode

class Lifter:

    def __init__(self, prog):
        self.program = prog
        self.emitter = codeEmitter.CodeEmitter()
        self._prefix = None

    def emit(self, text):
        self.emitter.emit(text)

    def emitline(self, text):
        self.emitter.emitline(text)

    def getCode(self):
        return str(self.emitter)

    def doLifting(self):
        for i in self.program.instructionList:
            self.lift(i)

    def lift(self, inst):

        opcode = inst.getOpcode()

        # only process prefix for certain operations
        if self._prefix and inst.operation.opcode not in [Opcode.CallFunction, Opcode.UnaryOperation, Opcode.BinaryOperation]:
            self._prefix = None

        if opcode == Opcode.LoadInteger or \
            opcode == Opcode.LoadFloat or \
            opcode == Opcode.LoadBoolean:

            self.emitline(str(inst.getOutput()) + " = " + str(inst.operation.value))

        if opcode == Opcode.LoadString:
            self.emitline(str(inst.getOutput()) + " = \"" + str(inst.operation.value)+"\"")

        if opcode == Opcode.Nop:
            pass

        if opcode == Opcode.BeginFunction:
            output = inst.getOutput()
            signature = inst.operation.signature
            args = inst.getAllTemps()

            code = str(output) + " = function( "
            code += ", ".join([str(x) for x in args])
            code += ") "

            outerVars = signature.getOuterVars()
            # print outerVars
            if len(outerVars) > 0:
                code += "use ("
                for var in outerVars:
                    code += str(var)+", "
                if code[-2:] == ', ':
                    code = code[:-2]
                code += " ){"
            else:
                code += "{"

            self.emit(code)
            self.emitter.increaseIndentLevel()

        if opcode == Opcode.EndFunction:
            self.emitter.decreaseIndentLevel()
            self.emitline("}")


        if opcode == Opcode.CallFunction:
            output = str(inst.getOutput())
            func = inst.getInput()

            inp_code = str(func)+"( "
            inp_code += ", ".join([str(x) for x in inst.getAllInputs()[1:]])
            inp_code += ")"
            if self._prefix:
                inp_code = f"{self._prefix}.({inp_code})"
                self._prefix = None
            code = f"{output} = {inp_code}"

            self.emitline(code)

        if opcode == Opcode.LoadNull:
            self.emitline(str(inst.getOutput()) + " = null")

        if opcode == Opcode.Return:
            self.emitline("return " + str(inst.getInput()))

        if opcode == Opcode.BeginIf:
            self.emit("if(" + str(inst.getInput(0)) + "){")
            self.emitter.increaseIndentLevel()

        if opcode == Opcode.BeginElse:
            self.emitter.decreaseIndentLevel()
            self.emit("}else{")
            self.emitter.increaseIndentLevel()

        if opcode == Opcode.EndIf:
            self.emitter.decreaseIndentLevel()
            self.emit("}")

        if opcode == Opcode.Break:
            self.emitline("break")

        if opcode == Opcode.Continue:
            self.emitline("continue")

        if opcode == Opcode.UnaryOperation:
            code = str(inst.getInput()) + " = "
            altCode = str(inst.getOutput()) + " = "
            commonCode = ""
            op = inst.operation.op
            if op == operation.UnaryOperator.Inc:
                commonCode = str(inst.getInput())+ " + 1"
            if op == operation.UnaryOperator.Dec:
                commonCode = str(inst.getInput())+ " - 1"
            if op == operation.UnaryOperator.BitwiseNot:
                commonCode = str(inst.operation.op) + str(inst.getInput())
            if op == operation.UnaryOperator.LogicalNot:
                commonCode = str(inst.operation.op) + str(inst.getInput())

            if self._prefix:
                commonCode = f"{self._prefix}.({commonCode})"
            code += commonCode
            altCode += commonCode
            self.emitline(code)
            self.emitline(altCode)
            self._prefix = None

        if opcode == Opcode.BinaryOperation:
            out = str(inst.getOutput())
            inp1 = str(inst.getInput(0))
            inp2 = str(inst.getInput(1))

            op = inst.operation.op
            if(op == operation.BinaryOperator.LShift or op == operation.BinaryOperator.RShift):
                code = inp1 + str(inst.operation.op) + inp2
                if self._prefix:
                    code = f"{self._prefix}.({code})"
                    self._prefix = None
                code = "if("+inp2+">0){"+ out + " = " + code + ";" +"}"
                self.emit(code)
            else:
                code = inp1 + str(inst.operation.op) + inp2
                if self._prefix:
                    code = f"{self._prefix}.({code})"
                self.emitline(out+" = " + code)

            self._prefix = None


        if opcode == Opcode.BeginFor:
            loopvar = inst.getTemp()
            start = inst.getInput(0)
            end = inst.getInput(1)
            step = inst.getInput(2)

            code = "for("
            code += str(loopvar) + " = " + str(start) + "; "
            code += str(loopvar) + " < " + str(end) + " ; "
            code += str(loopvar) + " = " + str(loopvar) + " + " + str(step)

            self.emit(code + "){")
            self.emitter.increaseIndentLevel()


        if opcode == Opcode.EndFor:
            self.emitter.decreaseIndentLevel()
            self.emit("}")

        if opcode == Opcode.BeginWhile:
            inp = str(inst.getInput(0)) + str(inst.operation.comparater) + str(inst.getInput(1))
            self.emit("while (" + inp + "){")
            self.emitter.increaseIndentLevel()

        if opcode == Opcode.EndWhile:
            self.emitter.decreaseIndentLevel()
            self.emit("}")

        if opcode == Opcode.BeginDoWhile:
            self.emit("do{")
            self.emitter.increaseIndentLevel()

        if opcode == Opcode.EndDoWhile:
            self.emitter.decreaseIndentLevel()
            inp = str(inst.getInput(0)) + str(inst.operation.comparater) + str(inst.getInput(1))
            self.emitline("}while(" + inp + ")")


        if opcode == Opcode.Include:
            self.emitline("include "+str(inst.getInput()))

        if opcode == Opcode.Copy:
            inp1 = str(inst.getInput(0))
            inp2 = str(inst.getInput(1))
            self.emitline(inp1 + " = " + inp2)

        if opcode == Opcode.Phi:
            out = str(inst.getOutput())
            inp = str(inst.getInput())
            self.emitline(out + " = " + inp)

        if opcode == Opcode.BeginTry:
            self.emit("try{")
            self.emitter.increaseIndentLevel()

        if opcode == Opcode.BeginCatch:
            self.emitter.decreaseIndentLevel()
            self.emit("}catch(Exception $e){")
            self.emitter.increaseIndentLevel()

        if opcode == Opcode.EndTryCatch:
            self.emitter.decreaseIndentLevel()
            self.emit("}")

        if opcode == Opcode.CreateArray:
            code = str(inst.getOutput()) + " = "
            if probability.Random.probability(0.5):
                code += "[" + ", ".join([str(x) for x in inst.getAllInputs()]) + "]"
            else:
                code += "Array (" + ", ".join([str(x) for x in inst.getAllInputs()]) + ")"

            self.emitline(code)

        if opcode == Opcode.CreateDict:
            code = str(inst.getOutput()) + " = "
            if probability.Random.probability(0.5):
                code += "["
                for key, value in inst.getAllInputs():
                    code += str(key) + " => " + str(value) + ", "
                if code[-2:] == ", ":
                    code = code[:-2]
                code += "]"
            else:
                code += "Array("
                for key, value in inst.getAllInputs():
                    code += str(key) + " => " + str(value) + ", "
                if code[-2:] == ", ":
                    code = code[:-2]
                code += ")"

            self.emitline(code)

        if opcode == Opcode.GetArrayElem:
            code = str(inst.getOutput()) + " = "
            code += str(inst.getInput(0)) + "[" + str(inst.getInput(1)) + "]"
            self.emitline(code)

        if opcode == Opcode.SetArrayElem:
            code = str(inst.getInput(0)) + "[" + str(inst.getInput(1)) + "]"
            code += " = " + str(inst.getInput(2))
            self.emitline(code)

        if opcode == Opcode.VarPrefix:
            self._prefix = inst.inputs[0]

if __name__ == '__main__':
    def main():
        prog = program.Program([
            instructions.Instruction(operation.LoadInteger(10),False,[variable.Variable(0)]),
            instructions.Instruction(operation.LoadFloat(1.1),False,[variable.Variable(1)]),
            instructions.Instruction(operation.LoadBoolean(True),False,[variable.Variable(1)]),
            instructions.Instruction(operation.LoadString("qweqweqweqwe"),False,[variable.Variable(0)]),
            instructions.Instruction(operation.BeginIf(),[variable.Variable(2)]),
            instructions.Instruction(operation.BeginElse()),
            instructions.Instruction(operation.EndIf())

        ])

        prog = program.Program([
            instructions.Instruction(operation.LoadString("phar"),False,[variable.Variable(100)]),
            instructions.Instruction(operation.Include(),[variable.Variable(100)]),
            instructions.Instruction(operation.Include(),[variable.Variable(100)]),

            instructions.Instruction(operation.LoadInteger(1),False,[variable.Variable(0)]),
            instructions.Instruction(operation.BeginFunction(typesData.FunctionSignature(2)),False,[variable.Variable(1)],[variable.Variable(10),variable.Variable(11)]),
            instructions.Instruction(operation.BinaryOperation("+"),[variable.Variable(10),variable.Variable(11)],[variable.Variable(2)]),
            instructions.Instruction(operation.LoadString("somestring"),False,[variable.Variable(3)]),
            instructions.Instruction(operation.Return(),[variable.Variable(2)]),
            instructions.Instruction(operation.EndFunction()),
            instructions.Instruction(operation.LoadInteger(1337),False,[variable.Variable(4)]),
            instructions.Instruction(operation.CallFunction(2),[variable.Variable(1), variable.Variable(4), variable.Variable(0)],[variable.Variable(6)]),
            instructions.Instruction(operation.LoadInteger(1337),False,[variable.Variable(7)]),
            instructions.Instruction(operation.Break()),
            instructions.Instruction(operation.Continue()),
            instructions.Instruction(operation.UnaryOperation("++"),[variable.Variable(0)],[variable.Variable(0)]),
        ])


        prog = program.Program([
            instructions.Instruction(operation.LoadString("phar"),False,[variable.Variable(100)]),
            instructions.Instruction(operation.Include(),[variable.Variable(100)]),
            instructions.Instruction(operation.Include(),[variable.Variable(100)]),

            instructions.Instruction(operation.LoadInteger(0), False, [variable.Variable(0)]),
            instructions.Instruction(operation.LoadInteger(1), False, [variable.Variable(1)]),
            instructions.Instruction(operation.LoadInteger(10), False, [variable.Variable(2)]),
            instructions.Instruction(operation.LoadInteger(10), False, [variable.Variable(3)]),
            instructions.Instruction(operation.LoadInteger(20), False, [variable.Variable(4)]),
            instructions.Instruction(operation.LoadInteger(5), False, [variable.Variable(5)]),
            instructions.Instruction(operation.LoadInteger(50), False, [variable.Variable(8)]),
            instructions.Instruction(operation.Phi(), [variable.Variable(3)], [variable.Variable(6)]),
            instructions.Instruction(operation.Phi(), [variable.Variable(4)], [variable.Variable(7)]),
            instructions.Instruction(operation.BeginFor("++", "<"), [variable.Variable(0),variable.Variable(2),variable.Variable(8)], False, [variable.Variable(80)]),
            instructions.Instruction(operation.BinaryOperation("<"), [variable.Variable(8), variable.Variable(5)], [variable.Variable(6)]),
            instructions.Instruction(operation.BeginIf(), [variable.Variable(6)], False),
            instructions.Instruction(operation.LoadInteger(0), False, [variable.Variable(9)]),
            instructions.Instruction(operation.BeginWhile("<"),[variable.Variable(9), variable.Variable(5)], False ),
            instructions.Instruction(operation.BinaryOperation("+"), [variable.Variable(6), variable.Variable(1)], [variable.Variable(10)]),
            instructions.Instruction(operation.Copy(), [variable.Variable(6), variable.Variable(10)]),
            instructions.Instruction(operation.BinaryOperation("+"), [variable.Variable(9), variable.Variable(1)], [variable.Variable(11)]),
            instructions.Instruction(operation.Copy(), [variable.Variable(6), variable.Variable(10)]),
            instructions.Instruction(operation.EndWhile(), False, False),

            instructions.Instruction(operation.BeginElse(), False, False),
            instructions.Instruction(operation.LoadInteger(0), False, [variable.Variable(9)]),
            instructions.Instruction(operation.BeginWhile("<"),[variable.Variable(9), variable.Variable(5)], False ),
            instructions.Instruction(operation.BinaryOperation("+"), [variable.Variable(7), variable.Variable(1)], [variable.Variable(10)]),
            instructions.Instruction(operation.Copy(), [variable.Variable(7), variable.Variable(10)]),
            instructions.Instruction(operation.BinaryOperation("+"), [variable.Variable(9), variable.Variable(1)], [variable.Variable(11)]),
            instructions.Instruction(operation.Copy(), [variable.Variable(6), variable.Variable(10)]),
            instructions.Instruction(operation.EndWhile(), False, False),

            instructions.Instruction(operation.EndIf(), False, False),
            instructions.Instruction(operation.EndFor(), False, False),
            instructions.Instruction(operation.LoadInteger(1),False,[variable.Variable(90)]),
        ])
        # print prog
        l = Lifter(prog)
        l.doLifting()
        print(l.emitter)
    main()
