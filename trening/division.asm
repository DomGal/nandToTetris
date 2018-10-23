// load values in R0 and R1
// program computes R0 / R1
// and returnes quotient in R2
// and remainder in R3
// (R0 - R3) / R1 = R2


@R0
D = M

@R1
D = D - M

@RETURN_PRIOR   // if R0 < R1 return 0 with remainder R0
D;JEQ

@counter
M = 0

@R0
D = M

@leftover
M = D

(LOOP)
    @R1
    D = M

    @leftover
    D = M - D

    @IF_ZERO
    D;JEQ

    @IF_NEGATIVE
    D;JLT

    @counter
    M = M + 1

    @R1
    D = M

    @leftover
    M = M - D

    @LOOP
    0;JMP    


(RETURN_PRIOR)
    @R2
    M = 0

    @R0
    D = M

    @R3
    M = D

    @END
    0;JMP

(IF_ZERO)
    @counter
    D = M + 1

    @R2
    M = D

    @R3
    M = 0

    @END
    0;JMP


(IF_NEGATIVE)
    @leftover
    D = M
    @R3
    M = D

    @counter
    D = M
    @R2
    M = D

    @END
    0;JMP



(END)
@END
0;JMP