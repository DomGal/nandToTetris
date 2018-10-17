"""
This is assembler program for hack computer developed for nand2tetris coursera course
"""
from enum import Enum
import argparse
from pathlib import Path
from pathlib import PurePath
import time

class CommandType(Enum):
    """
    Enum for command type
    """
    A_COMMAND = 0
    C_COMMAND = 1
    L_COMMAND = 2

class Command:
    """
    This class handles single command
    """
    def __init__(self, inLine, lineNumber):
        self.line = inLine
        self.lineNumber = lineNumber
        self.commandType = None

    def getCommandType(self):
        if self.commandType:
            pass
        else:
            if self.line[0] == "@":
                self.commandType = CommandType.A_COMMAND
            elif (self.line.find("=") != -1) or (self.line.find(";") != -1):
                self.commandType = CommandType.C_COMMAND
            elif (self.line[0] == "(") and (self.line[-1] == ")"):
                self.commandType = CommandType.L_COMMAND
            else:
                raise ValueError("Error on line number {}: {} Command must be A command, C command or label".format(self.lineNumber, self.line))
        return self.commandType

    def __parseACommand(self):
        return self.line[1:]

    def __parseLCommand(self):
        return self.line[1:-1]

    def __parseCCommand(self):
        cLine = self.line
        if cLine.find("=") != -1:
            dest, cLine = tuple(cLine.split("="))
        else:
            dest = "null"
        if cLine.find(";") != -1:
            comp, jump = tuple(cLine.split(";"))
        else:
            comp = cLine
            jump = "null"
        returnDict = {
            "dest" : dest,
            "comp" : comp,
            "jump" : jump
        } 
        return returnDict


    def parse(self):
        if self.getCommandType() == CommandType.A_COMMAND:
            return self.__parseACommand()
        elif self.getCommandType() == CommandType.C_COMMAND:
            return self.__parseCCommand()
        else:
            return self.__parseLCommand()


    def isSymbolic(self):
        if self.getCommandType() == CommandType.A_COMMAND:
            value = self.parse()
            return not value.isdigit()
        else:
            return False

    def __getCompCommandsDict(self):
        compCommandsDict = {
            # a = 0
            "0":   "0101010",
            "1":   "0111111",
            "-1":  "0111010",
            "D":   "0001100",
            "A":   "0110000",
            "!D":  "0001101",
            "!A":  "0110001",
            "-D":  "0001111",
            "-A":  "0110011",
            "D+1": "0011111",
            "A+1": "0110111",
            "D-1": "0001110",
            "A-1": "0110010",
            "D+A": "0000010",
            "D-A": "0010011",
            "A-D": "0000111",
            "D&A": "0000000",
            "D|A": "0010101",
            # a = 1
            "M":   "1110000",
            "!M":  "1110001",
            "-M":  "1110011",
            "M+1": "1110111",
            "M-1": "1110010",
            "D+M": "1000010",
            "D-M": "1010011",
            "M-D": "1000111",
            "D&M": "1000000",
            "D|M": "1010101",
        }
        return compCommandsDict



    def __getDestCommandsDict(self):
        destComandsDict = {
            "null": "000",
            "M":    "001",
            "D":    "010",
            "MD":   "011",
            "A":    "100",
            "AM":   "101",
            "AD":   "110",
            "AMD":  "111"
        }
        return destComandsDict
    
    def __getJumpCommandsDict(self):
        jumpCommandsDict = {
            "null": "000",
            "JGT":  "001",
            "JEQ":  "010",
            "JGE":  "011",
            "JLT":  "100",
            "JNE":  "101",
            "JLE":  "110",
            "JMP":  "111"
        }
        return jumpCommandsDict

    def __aCommandToBinary(self, symbolsDict):
        if self.isSymbolic():
            value = symbolsDict[self.parse()]
        else:
            value = self.parse()
        
        binaryValue = "0" + (15 * "0" + "{0:b}".format(int(value)))[-15:]
        return binaryValue

    def __cCommandToBinary(self):
        prefix = "111"
        valueDict = self.parse()
        destBinary = self.__getDestCommandsDict()[valueDict["dest"]]
        compBinary = self.__getCompCommandsDict()[valueDict["comp"]]
        jumpBinary = self.__getJumpCommandsDict()[valueDict["jump"]]

        binaryValue = prefix + compBinary + destBinary + jumpBinary

        return binaryValue

    def __lCommandToBinary(self):
        pass
        return None

    def translateToBinary(self, symbolsDict):
        if self.getCommandType() == CommandType.A_COMMAND:
            return self.__aCommandToBinary(symbolsDict)
        elif self.getCommandType() == CommandType.C_COMMAND:
            return self.__cCommandToBinary()
        else:
            raise ValueError("File not preprocessed correctly!")

# End of class Command


class Preprocessor:
    """
    This class is used to remove comments, remove whitespaces, and
    detect and catalog symbols
    """
    def __init__(self, fileList):
        self.fileList = fileList
        # add next ref ,so you know which value to assign
        self.symbolsDict = self.__getDefaultSymbolsDict()
        self.labelsDict = {}
        self.nextRef = 0
        self.fileListClean = []
        self.lineNumber = 0


    def __getDefaultSymbolsDict(self):
        registerRefs = {f"R{i}" : i for i in range(16)}
        namedRefs = {
            "SP" :    0,
            "LCL":    1,
            "ARG":    2,
            "THIS":   3,
            "THAT":   4,
            "SCREEN": 16384,
            "KBD":    24576
        }
        # this only works in >= python 3.5
        # else use symbolsDict = registerRefs.copy().update(namedRefs)
        symbolsDict = {**registerRefs, **namedRefs}
        return symbolsDict


    def process(self):

        for line in self.fileList:
            index = line.find("//")
            if index == -1:
                slice = line
            else:
                slice = line[:index]
            cLine = "".join(slice.split())
            if cLine == "":
                continue

            currentCommand = Command(cLine, self.lineNumber)
            # putting l commands in symbolic table (dict)
            if currentCommand.getCommandType() == CommandType.L_COMMAND:
                value = currentCommand.parse()
                if value in self.labelsDict.keys():
                    raise ValueError("line: {}, label {} declared multiple times".format(self.lineNumber, value))
                self.labelsDict[value] = self.lineNumber
                continue

            self.fileListClean.append(cLine)
            self.lineNumber += 1
        # due to oversight in architecture, this is done in two passes insted of one
        for lineNumber, line in enumerate(self.fileListClean):
            #putting a commands in symbolic table (dict)
            currentCommand = Command(line, lineNumber)
            if currentCommand.getCommandType() == CommandType.A_COMMAND:
                value = currentCommand.parse()
                # if value is symbolic and not seen before put it in dict
                if (currentCommand.isSymbolic() and value not in self.symbolsDict.keys()
                    and value not in self.labelsDict.keys()):
                    while(self.nextRef in self.symbolsDict.values()):
                        self.nextRef += 1

                    self.symbolsDict[value] = self.nextRef
                    self.nextRef += 1
        
        self.symbolsDict.update(self.labelsDict)
        return self.fileListClean, self.symbolsDict

# End of class Preprocessor

class Parser:
    """
    This class parses preprocessed file and turns it into binary
    """
    # it is case sensitive
    def __init__(self, preprocessedFile, symbolsDict):
        self.inFile = preprocessedFile
        self.symbolsDict = symbolsDict
        self.binaryFile = []

    def toBinary(self):
        for lineNumber, line in enumerate(self.inFile):
            currentCommand = Command(line, lineNumber)
            binaryCommand = currentCommand.translateToBinary(self.symbolsDict)
            self.binaryFile.append(binaryCommand)
        return self.binaryFile

# End of class Parser


def main():
    argumentParser = argparse.ArgumentParser(description = "Assembler for hack computer.")
    argumentParser.add_argument("inputFile", metavar = "inFile", type = str, nargs = 1,
                                help = "location of input file.")
    #argumentParser.add_argument("outputFile", metavar = "outFile", type = str, nargs = 1,
    #                            help = "name of output file.")
    argumentParser.add_argument("--keep", action = "store_const", const = True,
                                help = "keep temporary preprocessed file")

    args = vars(argumentParser.parse_args())
    inFilePath = Path(args["inputFile"][0])
    #inFile = str(inFilePath.resolve())

    outFile = inFilePath.resolve().parent.joinpath(inFilePath.stem + ".hack")
    outFileTemp = inFilePath.resolve().parent.joinpath(inFilePath.stem + ".ohack")

    preprocessor = Preprocessor(inFilePath.open().readlines())
    preprocessedFile, symbolsDict = preprocessor.process()

    open(outFileTemp, mode = "w").write("\n".join(preprocessedFile))

    parser = Parser(preprocessedFile, symbolsDict)
    binaryFile = parser.toBinary()
    
    open(outFile, mode = "w").write("\n".join(binaryFile))

    return None


if __name__ == "__main__":
    tick = time.time()
    print("Hack Assembler starting")
    main()
    timeDelta = (time.time() - tick)
    print("Hack Assembler finished.\nDuration: {} ms.".format(int(timeDelta * 1000)))