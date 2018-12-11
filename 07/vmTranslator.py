import logging
from enum import Enum
import argparse
import os
from pathlib import Path, PurePath
import time

#--log=INFO -> loglevel
#getattr(logging, loglevel.upper)
logging.basicConfig(filename = "./vmTranslator.log",
    format = "%(asctime)s - %(levelname)s: %(message)s",
    level = logging.DEBUG)

class Stack:
    def __init__(self):
        self.__stackLength = 0
        self.__pointer = "SP"

    def __addComment(self, comment):
        return "// {}\n".format(comment)

    def __increaseStackPointer(self) -> str:
        command = "@{}\nM=M+1\n".format(self.__pointer)
        self.__stackLength += 1
        logging.debug("SP: {}".format(self.__stackLength))
        return command

    def __decreaseStackPinter(self) -> str:
        command = "@{}\nM=M-1\n".format(self.__pointer)
        self.__stackLength -= 1
        logging.debug("SP: {}".format(self.__stackLength))
        if self.__stackLength < 0:
            logging.warning("trying to decrease empty stack")
        return command

    def __dereferencePointer(self) -> str:
        """
        Place pointer value in D register
        """
        command = "@{}\nA=M\nD=M\n".format(self.__pointer)
        return command
    
    def __injectToAddress(self) -> str:
        """
        Place value from D register on address
        """
        # what if  value in D is negative?
        command = "@{}\nA=M\nM=D\n".format(self.__pointer)
        return command

    
    def pop(self):
        """
        We place poped value to D register
        """
        command = self.__addComment("stack pop")
        command += self.__decreaseStackPinter()
        command += self.__dereferencePointer()
        return command

    def push(self):
        """
        We assume the value we wish to push is located in D register
        """
        command = self.__addComment("stack push")
        command += self.__injectToAddress()
        command += self.__increaseStackPointer()
        return command

# end of class Stack

class SegmentType(Enum):
    """
    Enum for segment type
    """
    LCL_SEGMENT = 0
    ARG_SEGMENT = 1
    THIS_SEGMENT = 2
    THAT_SEGMENT = 3
    STATIC_SEGMENT = 4
    TEMP_SEGMENT = 5
    CONST_SEGMENT = 6
    POINTER_SEGMENT = 7

# end of class SegmentType

class MemorySegmentManager:
    """
    docstring
    """

    def __init__(self, fileName, *, tempAddress = 5) -> None:
        self.__fileName = fileName
        self.__tempAddress = int(tempAddress)
        self.__auxLabels = ["R{}".format(13 + i) for i in range(2)]
        self.__segmentsConverterDict = {
            SegmentType.LCL_SEGMENT: "LCL",
            SegmentType.ARG_SEGMENT: "ARG",
            SegmentType.THIS_SEGMENT: "THIS",
            SegmentType.THAT_SEGMENT: "THAT",
        }
    
    def getAuxLabelsList__(self):
        return self.__auxLabels.copy()

    def __resolveAddress(self, segment: str, offset: str) -> str:
        command = "@{}\nD=A\n@{}\nD=D+M\n".format(offset, segment)
        return command
    
    def writeToAddress(self, address: str) -> str:
        command = "@{}\nM=D\n".format(address)
        return command

    def readFromAddress(self, address: str) -> str:
        command = "@{}\nD=M\n".format(address)
        return command
    
    def writeToPointer(self, pointerAddress: str) -> str:
        command = "@{}\nA=M\nM=D\n".format(pointerAddress)
        return command

    def readFromPointer(self, pointerAddress: str) -> str:
        command = "@{}\nA=M\nD=M\n".format(pointerAddress)
        return command

    def readValue(self, offset: str) -> str:
        command = "@{}\nD=A\n".format(offset)
        return command

    def readPointerFromRegister(self) -> str:
        command = "A=D\nD=M\n"
        return command

    def __genericSetSegment(self, segment: str, offset: str) -> str:
        aux0 = str(self.__auxLabels[0])
        aux1 = str(self.__auxLabels[1])
        command = ""
        command += self.writeToAddress(aux0)
        command += self.__resolveAddress(segment, offset)
        command += self.writeToAddress(aux1)
        command += self.readFromAddress(aux0)
        command += self.writeToPointer(aux1)
        return command

    def __genericGetSegment(self, segment, offset):
        aux0 = str(self.__auxLabels[0])
        command = ""
        command += self.__resolveAddress(segment, offset)
        command += self.writeToAddress(aux0)
        command += self.readFromPointer(aux0)
        return command

    def __constGetSegment(self, offset):
        command = ""
        command += self.readValue(offset)
        return command

    def __staticSetSegment(self, offset):
        command = "@{}.{}\nM=D\n".format(self.__fileName, offset)
        return command

    def __staticGetSegment(self, offset):
        command = "@{}.{}\nD=M\n".format(self.__fileName, offset)
        return command

    def __tempResolveAddress(self, offset):
        numOffset = int(offset)
        isInBounds =  (1 <= numOffset <= 8)
        if not isInBounds:
            logging.error("Temp offset out of bounds")
            raise ValueError
        numOffset = int(offset)
        numTempBase = self.__tempAddress
        resolvedAddress = str(numTempBase + numOffset)
        return resolvedAddress

    def __tempSetSegment(self, offset):
        resolvedAddress = self.__tempResolveAddress(offset)
        command = self.writeToAddress(resolvedAddress)
        return command

    def __tempGetSegemnt(self, offset):
        resolvedAddress = self.__tempResolveAddress(offset)
        command = self.readFromAddress(resolvedAddress)
        return command

    def __pointerResolveOffset(self, offset):
        """
        resolves offset for pointer segment
        """
        if offset == "0":
            segment = "THIS"
        elif offset == "1":
            segment = "THAT"
        else:
            logging.error("Invalid offset specified")
            raise ValueError
        return segment

    def __pointerSetSegment(self, offset):
        segment = self.__pointerResolveOffset(offset)
        return self.writeToAddress(segment)

    def __pointerGetSegment(self, offset):
        segment = self.__pointerResolveOffset(offset)
        return self.readFromAddress(segment)

    def setSegment(self, rawSegment, offset):
        """
        Takes value form D register and places it to given
        segment and offset
        """
        if rawSegment in self.__segmentsConverterDict.keys():
            segment = self.__segmentsConverterDict[rawSegment]
            return self.__genericSetSegment(segment, offset)
        elif rawSegment == SegmentType.STATIC_SEGMENT:
            return self.__staticSetSegment(offset)
        elif rawSegment == SegmentType.TEMP_SEGMENT:
            return self.__tempSetSegment(offset)
        elif rawSegment == SegmentType.POINTER_SEGMENT:
            return self.__pointerSetSegment(offset)
        else:
            logging.error("invalid segment passed")
            raise ValueError
        
    def getSegment(self, rawSegment, offset):
        """
        for given segment and offset, puts value in D register
        """
        if rawSegment in self.__segmentsConverterDict.keys():
            segment = self.__segmentsConverterDict[rawSegment]
            return self.__genericGetSegment(segment, offset)
        elif rawSegment == SegmentType.CONST_SEGMENT:
            return self.__constGetSegment(offset)
        elif rawSegment == SegmentType.STATIC_SEGMENT:
            return self.__staticGetSegment(offset)
        elif rawSegment == SegmentType.TEMP_SEGMENT:
            return self.__tempGetSegemnt(offset)
        elif rawSegment == SegmentType.POINTER_SEGMENT:
            return self.__pointerGetSegment(offset)
        else:
            logging.error("invalid segment passed")
            raise ValueError

    def __auxResolveOffset(self, offset):
        if int(offset) >= len(self.__auxLabels):
            logging.error("invalid Aux offset specified.")
            raise ValueError
        label = self.__auxLabels[int(offset)]
        return label

    def setAuxValue(self, offset):
        """
        sets value contained in D register to aux with given offset
        """
        label = self.__auxResolveOffset(offset)
        command = "@{}\nM=D\n".format(label)
        return command

    def getAuxValue(self, offset):
        """
        gets value from aux with given offset and places it in D register
        """
        label = self.__auxResolveOffset(offset)
        command = "@{}\nD=M\n".format(label)
        return command
    
    def getAuxReference(self, offset):
        label = self.__auxResolveOffset(offset)
        command = "@{}\n".format(label)
        return command

    def getLabelReference(self, label):
        command = "@{}\n".format(label)
        return command

# end of class MemorySegmentManager

class OperationsManager:
    def __init__(self, stack, memorySegmentManager):
        self.__stack = stack
        self.__memorySegmentManager = memorySegmentManager
        self.__labelId = 0

    def __addComment(self, comment):
        return "// {}\n".format(comment)

    def __getNextLabelId(self):
        nextLabelId = str(self.__labelId)
        self.__labelId += 1
        return nextLabelId

    def __addMemoryRegister(self):
        command = "D=D+M\n"
        return command

    def __subMemoryRegister(self):
        command = "D=D-M\n"
        return command

    def __negativeMemoryRegister(self):
        command = "D=-D\n"
        return command

    def __logicalAndMemoryRegister(self):
        command = "D=D&M\n"
        return command

    def __logicalOrMemoryRegister(self):
        command = "D=D|M\n"
        return command

    def __logicalNotMemoryRegister(self):
        command = "D=!D\n"
        return command
    
    def opAdd(self):
        msm = self.__memorySegmentManager
        stack = self.__stack
        command = self.__addComment("opAdd")
        command += stack.pop()
        command += msm.setAuxValue("0")
        command += stack.pop()
        command += msm.setAuxValue("1")
        command += msm.getAuxValue("0")
        command += msm.getAuxReference("1")
        command += self.__addMemoryRegister()
        command += stack.push()
        return command


    def opSub(self):
        msm = self.__memorySegmentManager
        stack = self.__stack
        command = self.__addComment("opSub")
        command += stack.pop()
        command += msm.setAuxValue("0")
        command += stack.pop()
        command += msm.setAuxValue("1")
        command += msm.getAuxValue("1")
        command += msm.getAuxReference("0")
        command += self.__subMemoryRegister()
        command += stack.push()
        return command
    
    def opNeg(self):
        stack = self.__stack
        command = self.__addComment("opNeg")
        command += stack.pop()
        command += self.__negativeMemoryRegister()
        command += stack.push()
        return command

    def __ifElseBranch(self, labelId, condition):
        if condition not in ["JEQ", "JLT", "JGT"]:
            logging.error("invalid condition in branching")
            raise ValueError
        ifBranch = "@IF.{}\nD;{}\n\t//ELSE\n\tD=0\n\t@END_IF.{}\n".format(
            labelId, condition, labelId)
        elseBranch = "\t0;JMP\n(IF.{})\n\t//IF\n\tD=-1\n(END_IF.{})\n".format(
            labelId, labelId)
        return ifBranch, elseBranch

    def opEq(self):
        """
        puts -1 in D registar if equal, else 0
        """
        stack = self.__stack
        ifLabelId = self.__getNextLabelId()
        ifBranch, elseBranch = self.__ifElseBranch(ifLabelId, "JEQ")
        command = self.__addComment("opEq")
        command += self.opSub()
        command += stack.pop()
        command += ifBranch
        command += elseBranch
        command += stack.push()
        return command

    
    def opGt(self):
        stack = self.__stack
        ifLabelId = self.__getNextLabelId()
        command = self.__addComment("opGt")
        ifBranch, elseBranch = self.__ifElseBranch(ifLabelId, "JGT")
        command += self.opSub()
        command += stack.pop()
        command += ifBranch
        command += elseBranch
        command += stack.push()
        return command

    def opLt(self):
        stack = self.__stack
        ifLabelId = self.__getNextLabelId()
        ifBranch, elseBranch = self.__ifElseBranch(ifLabelId, "JLT")
        command = self.__addComment("opLt")
        command += self.opSub()
        command += stack.pop()
        command += ifBranch
        command += elseBranch
        command += stack.push()
        return command

    def opAnd(self):
        stack = self.__stack
        msm = self.__memorySegmentManager
        command = self.__addComment("opAnd")
        command += stack.pop()
        command += msm.setAuxValue("0")
        command += stack.pop()
        command += msm.setAuxValue("1")
        command += msm.getAuxValue("0")
        command += msm.getAuxReference("1")
        command += self.__logicalAndMemoryRegister()
        command += stack.push()
        return command

    def opOr(self):
        stack = self.__stack
        msm = self.__memorySegmentManager
        command = self.__addComment("opOr")
        command += stack.pop()
        command += msm.setAuxValue("0")
        command += stack.pop()
        command += msm.setAuxValue("1")
        command += msm.getAuxValue("0")
        command += msm.getAuxReference("1")
        command += self.__logicalOrMemoryRegister()
        command += stack.push()
        return command

    def opNot(self):
        stack = self.__stack
        command = self.__addComment("opNot")
        command += stack.pop()
        command += self.__logicalNotMemoryRegister()
        command += stack.push()
        return command


    # branching and control flow commands
    def label(self, label):
        command = "({})\n".format(label)
        return command

    def ifGoto(self, label):
        stack = self.__stack
        msm = self.__memorySegmentManager
        command = self.__addComment("ifGoto")
        command += stack.pop()
        command += msm.getLabelReference(label)
        command += "D;JGT\n"
        return command

    def goto(self, label):
        msm = self.__memorySegmentManager
        command = self.__addComment("goto")
        command += msm.getLabelReference(label)
        command += "0;JMP\n"
        return command

    # function definition, call and return
    def __getReturnAddress(self, functionName):
        returnAddress = "{}$ret".format(functionName)
        return returnAddress

    def functionCall(self, functionName, numberOfArguments):
        stack = self.__stack
        msm = self.__memorySegmentManager
        returnAddress = self.__getReturnAddress(functionName)
        command = self.__addComment(
            "calling function {} with {} arguments".format(
                functionName, numberOfArguments
                )
            )
        # setting a caller frame
        command += self.__addComment("setting the caller frame")
        command += msm.readValue(returnAddress)
        command += stack.push()
        command += msm.readFromAddress("LCL")
        command += stack.push()
        command += msm.readFromAddress("ARG")
        command += stack.push()
        command += msm.readFromAddress("THIS")
        command += stack.push()
        command += msm.readFromAddress("THAT")
        command += stack.push()
        # resolving new segment pointers
        # ARG = SP - 5 - nArgs
        command += self.__addComment("resolve new segment pointers")
        command += msm.readValue("SP")
        command += stack.push()
        command += msm.readValue("5")
        command += stack.push()
        command += self.opSub()
        command += msm.readValue(numberOfArguments)
        command += stack.push()
        command += self.opSub()
        command += stack.pop()
        command += msm.writeToAddress("ARG")
        # LCL = SP
        command += self.__addComment("LCL=SP")
        command += msm.readValue("SP")
        command += msm.writeToAddress("LCL")
        # goto function name
        command += self.goto(functionName)
        # return label
        command += self.label(returnAddress)
        return command

    def functionDefinition(self, functionName, numberOfLocals):
        stack = self.__stack
        msm = self.__memorySegmentManager        
        command = self.__addComment(
            "definition of function {} with {} local arguments".format(
                functionName, numberOfLocals
                )
            )
        command += self.label(functionName)
        # set up local segment
        command += self.__addComment("set up local segment")
        command += msm.readValue("0")
        for _ in range(int(numberOfLocals)):
            command += stack.push()
        return command

    def __returnSegmentPointerFromFrame(self, endFrameLabel,
                                        offset, segmentLabel):
        stack = self.__stack
        msm = self.__memorySegmentManager
        command = self.__addComment("return segment pointer from frame")
        command += msm.readFromAddress(endFrameLabel)
        command += stack.push()
        command += msm.readValue(offset)
        command += self.opSub()
        command += stack.pop()
        command += msm.readPointerFromRegister()
        command += msm.writeToAddress(segmentLabel)
        return command

    def functionReturn(self):
        stack = self.__stack
        msm = self.__memorySegmentManager
        command = self.__addComment("function return")
        # put return value in arg
        command += self.__addComment("put return value in arg")
        command += stack.pop()
        command += msm.setSegment(SegmentType.ARG_SEGMENT, "0")
        # initialize new variables
        # set up pointer to the end of the frame
        command += self.__addComment("set up pointer to the end of the frame")
        command += msm.readValue("LCL")
        command += msm.writeToPointer("endFrame")
        # fetch return address
        command += self.__addComment("fetch return address")
        command += msm.readFromAddress("endFrame")
        command += stack.push()
        command += msm.readValue("5")
        command += stack.push()
        command += self.opSub()
        command += stack.pop()
        command += msm.readPointerFromRegister()
        command += msm.writeToAddress("retAddr")
        # SP = ARG + 1
        command += self.__addComment("SP = ARG + 1")
        command += msm.readFromAddress("ARG")
        command += stack.push()
        command += msm.readValue("1")
        command += stack.push()
        command += self.opAdd()
        command += stack.pop()
        command += msm.writeToAddress("SP")
        # THAT = *(endFrame - 1)
        command += self.__addComment("THAT = *(endFrame - 1)")
        command += self.__returnSegmentPointerFromFrame("endFrame",\
                        "1", "THAT")
        # THIS = *(endFrame - 2)
        command += self.__addComment("THIS = *(endFrame - 2)")
        command += self.__returnSegmentPointerFromFrame("endFrame",\
                        "2", "THIS")
        # ARG = *(endFrame - 3)
        command += self.__addComment("ARG = *(endFrame - 3)")
        command += self.__returnSegmentPointerFromFrame("endFrame",\
                        "3", "ARG")
        # LCL = *(endFrame - 4)
        command += self.__addComment("LCL = *(endFrame - 4)")
        command += self.__returnSegmentPointerFromFrame("endFrame",\
                        "4", "LCL")
        # goto retAddr
        command += self.goto("retAddr")
        # return final command
        return command

# end of class OperationsManager 

class Parser:
    def __init__(self, lineList, fileName):
        self.__lineList = lineList
        self.__fileName = fileName
        self.__stack = Stack()
        self.__msm = MemorySegmentManager(fileName)
        self.__opManager = OperationsManager(self.__stack, self.__msm)
        self.__validBranching = ["goto", "if-goto", "label"]
        self.__validFunctionOps = ["function", "call", "return"]
        self.__validStackOps = ["push", "pop"]
        self.__validALOps = ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]
        self.__validMemorySegments = ["argument", "local", "static", "constant",
            "this", "that", "pointer", "temp"]
        self.__memoryOpDict = None
        self.__stackOpDict = None
        self.__branchingDict = None
        self.__functionDict = None
        self.__alOpDict = None

    def __getMemoryOpDict(self):
        if self.__memoryOpDict is None:
            memoryOpDictSet = {
                "argument" : lambda offset: self.__msm.setSegment(SegmentType.ARG_SEGMENT, offset),
                "local" : lambda offset: self.__msm.setSegment(SegmentType.LCL_SEGMENT, offset),
                "static" : lambda offset: self.__msm.setSegment(SegmentType.STATIC_SEGMENT, offset),
                "this" : lambda offset: self.__msm.setSegment(SegmentType.THIS_SEGMENT, offset),
                "that" : lambda offset: self.__msm.setSegment(SegmentType.THAT_SEGMENT, offset),
                "pointer" : lambda offset: self.__msm.setSegment(SegmentType.POINTER_SEGMENT, offset),
                "temp" : lambda offset: self.__msm.setSegment(SegmentType.TEMP_SEGMENT, offset)
            }

            memoryOpDictGet = {
                "argument" : lambda offset: self.__msm.getSegment(SegmentType.ARG_SEGMENT, offset),
                "local" : lambda offset: self.__msm.getSegment(SegmentType.LCL_SEGMENT, offset),
                "static" : lambda offset: self.__msm.getSegment(SegmentType.STATIC_SEGMENT, offset),
                "constant" : lambda offset: self.__msm.getSegment(SegmentType.CONST_SEGMENT, offset),
                "this" : lambda offset: self.__msm.getSegment(SegmentType.THIS_SEGMENT, offset),
                "that" : lambda offset: self.__msm.getSegment(SegmentType.THAT_SEGMENT, offset),
                "pointer" : lambda offset: self.__msm.getSegment(SegmentType.POINTER_SEGMENT, offset),
                "temp" : lambda offset: self.__msm.getSegment(SegmentType.TEMP_SEGMENT, offset)
            }

            self.__memoryOpDict = {
                "pop" : memoryOpDictSet,
                "push" : memoryOpDictGet
            }
            logging.debug(self.__memoryOpDict.keys())
            logging.debug(self.__memoryOpDict["pop"].keys())
        return self.__memoryOpDict.copy()

    def __getStackOpDict(self):
        if self.__stackOpDict is None:
            stackOpDict = {
                "push" : self.__stack.push,
                "pop" : self.__stack.pop
            }
            self.__stackOpDict = stackOpDict
        return self.__stackOpDict.copy()

    def __getBranchingDict(self):
        if self.__branchingDict is None:
            branchingDict = {
                "goto" : self.__opManager.goto,
                "if-goto" : self.__opManager.ifGoto,
                "label" : self.__opManager.label
            }
            self.__branchingDict = branchingDict
        return self.__branchingDict.copy()

    def __getFunctionDict(self):
        if self.__functionDict is None:
            functionDict = {
                "function" : self.__opManager.functionDefinition,
                "call" : self.__opManager.functionCall,
                "return" : self.__opManager.functionReturn
            }
            self.__functionDict = functionDict
        return self.__functionDict.copy()

    def __getALOpDict(self):
        if self.__alOpDict is None:
            alOpDict = {
                "add" : self.__opManager.opAdd,
                "sub" : self.__opManager.opSub,
                "neg" : self.__opManager.opNeg,
                "eq"  : self.__opManager.opEq,
                "gt"  : self.__opManager.opGt,
                "lt"  : self.__opManager.opLt,
                "and" : self.__opManager.opAnd,
                "or"  : self.__opManager.opOr,
                "not" : self.__opManager.opNot 
            }
            self.__alOpDict = alOpDict
        return self.__alOpDict.copy()

    def __shouldBeProcessed(self, line):
        line = line.strip()
        if line == "":
            return False
        if line[:2] == "//":
            return False
        return True

    def __unpackLine(self, line):
        line = line.strip()
        commentIndex = line.find("//")
        if commentIndex == -1:
            return line
        line = line[:commentIndex].strip()
        return line
    
    def __parseLine(self, line, lineNumber):
        if not self.__shouldBeProcessed(line):
            return None
        line = self.__unpackLine(line)
        lineList = line.split()
        logging.debug("line: {}".format(lineNumber))

        command = ""

        if len(lineList) == 1:
            operation = lineList[0]
            if operation == "return":
                command += self.__getFunctionDict()["return"]()
            else:
                try:
                    command += self.__getALOpDict()[operation]()
                except:
                    logging.error("unknown operation '{}' on line: {}".format(operation, lineNumber))
                    raise ValueError
        elif len(lineList) == 2:
            branch, label = lineList
            if branch not in self.__validBranching:
                logging.error("invalid branch operation on line: {}".format(lineNumber))
                raise ValueError
            command += self.__getBranchingDict()[branch](label)
        elif len(lineList) == 3:

            if lineList[0] in self.__validFunctionOps:
                functionOp, functionName, parameterNumber = lineList
                command += self.__getFunctionDict()[functionOp](functionName, parameterNumber)

            else: 
                stackOp, segment, offset = lineList
                if stackOp not in self.__validStackOps:
                    logging.error("invalid stack operation on line: {}".format(lineNumber))
                    raise ValueError
                if segment not in self.__validMemorySegments:
                    logging.error("invalid memory segment on line: {}".format(lineNumber))
                    raise ValueError
            
                # check if order is ok, for instance if we do:
                #       > pop local 0
                # we pop from stack to D register and and set
                # local segment with offset 0 to value from D
                # register (previous value poped from stack)
                command += self.__getMemoryOpDict()[stackOp][segment](offset)
                if stackOp == "pop":
                    command = self.__getStackOpDict()["pop"]() + command
                else:
                    command += self.__getStackOpDict()["push"]()
        else:
            logging.error("invalid command on line: {}".format(lineNumber))
            ValueError
        return command

    def parse(self):
        lines = self.__lineList
        newLines = []
        for lineNumber, line in enumerate(lines):
            command = self.__parseLine(line, lineNumber)
            if command is not None:
                newLines.append("// {}".format(line))
                newLines.append(command)
        return newLines

# end of class Parser


def main():
    argumentParser = argparse.ArgumentParser(description = "Virtual machine translator.")
    argumentParser.add_argument("inputFile", metavar = "inFile", type = str, nargs = 1,
                                help = "location of input file.")

    argumentParser.add_argument("outputFile", metavar = "outFile", type = str, nargs = 1,
                                help = "name of output file.")

    argumentParser.add_argument("--keep", action = "store_const", const = True,
                                help = "keep temporary preprocessed file")

    args = vars(argumentParser.parse_args())
    inFilePath = Path(args["inputFile"][0])
    outFileName = args["outputFile"][0]

    if os.path.isfile(inFilePath):

        outFile = inFilePath.resolve().parent.joinpath(inFilePath.stem + ".asm")
        fileName = inFilePath.resolve().stem

    
        with open(inFilePath) as f:
            lines = f.readlines()

        processedFile = Parser(lines, fileName).parse()
    
        open(outFile, mode = "w").write("\n".join(processedFile))

    else:
        inFileNames = []
        for root, _, files in os.walk(inFilePath):
            for file in files:
                if file.endswith(".vm"):
                    if file == "Sys.vm":
                        inFileNames = [file] + inFileNames
                    else:
                        inFileNames.append(file)
        allLines = []
        for file in inFileNames:
            with open(os.path.join(root, file)) as f:
                allLines += f.readlines()
        processedFile = Parser(allLines, outFileName).parse()
        open(os.path.join(root, "{}.asm".format(outFileName)), mode = "w").write("\n".join(processedFile))

    return None


if __name__ == "__main__":
    tick = time.time()
    print("vm Translator starting\n")
    main()
    timeDelta = (time.time() - tick)
    print("vm Translator finished.\nDuration: {} ms.\n".format(int(timeDelta * 1000)))
