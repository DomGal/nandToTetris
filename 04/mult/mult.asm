// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// Put your code here.


//@R0
//D = M
//@counter
//M = D
//@R1
//D = M
//@R3
//M = D

//(LOOP)
//    @counter
//    M = M - 1
//    @END
//    M;JEQ
//
//    @R3
//    M = M + D

//    @LOOP
//    0;JMP

//(END)
//    @END
//    0;JMP


// set product to zero
@R2
M = 0

// set counter to value in R1
@R1
D = M
@counter
M = D

// if counter is zero break
@END
D;JEQ

// set factor to value in R0 this is done to prevent
// changing value in R0 and R1
@R0
D = M
@factor
M = D


// add factor counter times
(LOOP)
    @factor
    D = M
    @R2
    M = M + D
    @counter
    M = M - 1
    D = M
    
    @END
    D;JEQ

    @LOOP
    0;JMP

(END)
    @END
    0;JMP
