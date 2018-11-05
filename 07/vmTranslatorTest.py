import unittest

from vmTranslator import Stack, MemorySegmentManager, SegmentType

class StackTest(unittest.TestCase):

    def test_push(self):
        command = Stack().push()
        expectedCommand = "@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        self.assertEqual(command, expectedCommand, msg = "stack push test")

    def test_pop(self):
        command = Stack().pop()
        expectedCommand = "@SP\nM=M-1\n@SP\nA=M\nD=M\n"
        self.assertEqual(command, expectedCommand, msg = "stack pop test")

class MemorySegmentManagerTest(unittest.TestCase):

    def test_getLCL(self):
        msm = MemorySegmentManager("testFile")
        command = msm.getSegment(SegmentType.LCL_SEGMENT, "offset")
        expectedCommand = "@offset\nD=A\n@LCL\nD=D+M\n@aux0\nM=D\n@aux0\nA=M\nD=M\n"
        self.assertEqual(command, expectedCommand)

    def test_setLCL(self):
        msm = MemorySegmentManager("testFile")
        command = msm.setSegment(SegmentType.LCL_SEGMENT, "offset")
        expectedCommand = "@aux0\nM=D\n@offset\nD=A\n@LCL\nD=D+M\n@aux1\nM=D\n@aux0\nD=M\n@aux1\nA=M\nM=D\n"
        self.assertEqual(command, expectedCommand)

    def test_getARG(self):
        msm = MemorySegmentManager("testFile")
        command = msm.getSegment(SegmentType.ARG_SEGMENT, "offset")
        expectedCommand = "@offset\nD=A\n@ARG\nD=D+M\n@aux0\nM=D\n@aux0\nA=M\nD=M\n"
        self.assertEqual(command, expectedCommand)

    def test_setARG(self):
        msm = MemorySegmentManager("testFile")
        command = msm.setSegment(SegmentType.ARG_SEGMENT, "offset")
        expectedCommand = "@aux0\nM=D\n@offset\nD=A\n@ARG\nD=D+M\n@aux1\nM=D\n@aux0\nD=M\n@aux1\nA=M\nM=D\n"
        self.assertEqual(command, expectedCommand)

    def test_getTHIS(self):
        msm = MemorySegmentManager("testFile")
        command = msm.getSegment(SegmentType.THIS_SEGMENT, "offset")
        expectedCommand = "@offset\nD=A\n@THIS\nD=D+M\n@aux0\nM=D\n@aux0\nA=M\nD=M\n"
        self.assertEqual(command, expectedCommand)

    def test_setTHIS(self):
        msm = MemorySegmentManager("testFile")
        command = msm.setSegment(SegmentType.THIS_SEGMENT, "offset")
        expectedCommand = "@aux0\nM=D\n@offset\nD=A\n@THIS\nD=D+M\n@aux1\nM=D\n@aux0\nD=M\n@aux1\nA=M\nM=D\n"
        self.assertEqual(command, expectedCommand)

    def test_getTHAT(self):
        msm = MemorySegmentManager("testFile")
        command = msm.getSegment(SegmentType.THAT_SEGMENT, "offset")
        expectedCommand = "@offset\nD=A\n@THAT\nD=D+M\n@aux0\nM=D\n@aux0\nA=M\nD=M\n"
        self.assertEqual(command, expectedCommand)
    
    def test_setTHAT(self):
        msm = MemorySegmentManager("testFile")
        command = msm.setSegment(SegmentType.THAT_SEGMENT, "offset")
        expectedCommand = "@aux0\nM=D\n@offset\nD=A\n@THAT\nD=D+M\n@aux1\nM=D\n@aux0\nD=M\n@aux1\nA=M\nM=D\n"
        self.assertEqual(command, expectedCommand)

    def test_getCONST(self):
        msm = MemorySegmentManager("testFile")
        command = msm.getSegment(SegmentType.CONST_SEGMENT, "value")
        expectedCommand = "@value\nD=A\n"
        self.assertEqual(command, expectedCommand)

    def test_setSTATIC(self):
        msm = MemorySegmentManager("testFile")
        command = msm.setSegment(SegmentType.STATIC_SEGMENT, "offset")
        expectedCommand = "@testFile.offset\nM=D\n"
        self.assertEqual(command, expectedCommand)

    def test_getSTATIC(self):
        msm = MemorySegmentManager("testFile")
        command = msm.getSegment(SegmentType.STATIC_SEGMENT, "offset")
        expectedCommand = "@testFile.offset\nD=M\n"
        self.assertEqual(command, expectedCommand)
        
    def test_setPOINTER(self):
        msm = MemorySegmentManager("testFile")
        command = msm.setSegment(SegmentType.POINTER_SEGMENT, "0")
        expectedCommand = "@THIS\nM=D\n"
        self.assertEqual(command, expectedCommand)
        
        command = msm.setSegment(SegmentType.POINTER_SEGMENT, "1")
        expectedCommand = "@THAT\nM=D\n"
        self.assertEqual(command, expectedCommand)

    def test_getPOINTER(self):
        msm = MemorySegmentManager("testFile")
        command = msm.getSegment(SegmentType.POINTER_SEGMENT, "0")
        expectedCommand = "@THIS\nD=M\n"
        self.assertEqual(command, expectedCommand)

        command = msm.getSegment(SegmentType.POINTER_SEGMENT, "1")
        expectedCommand = "@THAT\nD=M\n"
        self.assertEqual(command, expectedCommand)

    def test_setTEMP(self):
        msm = MemorySegmentManager("testFile")
        for i in range(8):
            command = msm.setSegment(SegmentType.TEMP_SEGMENT, str(i + 1))
            expectedCommand = "@{}\nM=D\n".format(6 + i)
            self.assertEqual(command, expectedCommand)

    def test_getTEMP(self):
        msm = MemorySegmentManager("testFile")
        for i in range(8):
            command = msm.getSegment(SegmentType.TEMP_SEGMENT, str(i + 1))
            expectedCommand = "@{}\nD=M\n".format(6 + i)
            self.assertEqual(command, expectedCommand)

    def test_getAuxLabelsList(self):
        msm = MemorySegmentManager("testFile")
        labelsList = msm.getAuxLabelsList__()
        expectedLabelsList = ["aux{}".format(i) for i in range(5)]
        for label, expectedLabel in zip(labelsList, expectedLabelsList):
            self.assertEqual(label, expectedLabel)

    def test_getAuxReference(self):
        msm = MemorySegmentManager("testFile")
        for i in range(5):
            command = msm.getAuxReference(str(i))
            expectedCommand = "@aux{}\n".format(i)
            self.assertEqual(command, expectedCommand)

if __name__ == "__main__":
    unittest.main()