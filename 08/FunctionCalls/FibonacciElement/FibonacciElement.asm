@256
D=A
@SP
M=D
D=A
@SP
A=M
M=D
@SP
M=M+1
@LCL
D=M
@SP
A=M
M=D
@SP
M=M+1
@ARG
D=M
@SP
A=M
M=D
@SP
M=M+1
@THIS
D=M
@SP
A=M
M=D
@SP
M=M+1
@THAT
D=M
@SP
A=M
M=D
@SP
M=M+1
@5
D=A
@0
D=D+A
@SP
D=M-D
@ARG
M=D
@Sys.init
0;JMP
// function Main.fibonacci 0
(Main.fibonacci)
@SP
D=M
@LCL
M=D
@0
D=A
@SP
M=M+D
@Main.fibonacci$lcl_init_ignore
D;JEQ
@R13
M=D
@R14
M=0
(Main.fibonacci$lcl_init)
@R14
D=M
@LCL
A=D+M
M=0
@R14
MD=D+1
@R13
D=D-M
@Main.fibonacci$lcl_init
D;JLT
(Main.fibonacci$lcl_init_ignore)
// push argument 0
@0
D=A
@ARG
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push constant 2
@2
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
AM=M-1
D=M
A=A-1
D=M-D
@32767
A=A+1
D=D&A
@logi_lt_0
D;JEQ
D=-1
(logi_lt_0)
@SP
A=M-1
M=D
// if-goto IF_TRUE
@SP
AM=M-1
D=M
@Main.fibonacci$IF_TRUE
D;JNE
// goto IF_FALSE
@Main.fibonacci$IF_FALSE
0;JMP
// label IF_TRUE
(Main.fibonacci$IF_TRUE)
// push argument 0
@0
D=A
@ARG
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// return
@5
D=A
@LCL
A=M-D
D=M
@R13
M=D
@SP
A=M-1
D=M
@ARG
A=M
M=D
@ARG
D=M+1
@SP
M=D
@LCL
AM=M-1
D=M
@THAT
M=D
@LCL
AM=M-1
D=M
@THIS
M=D
@LCL
AM=M-1
D=M
@ARG
M=D
@LCL
AM=M-1
D=M
@LCL
M=D
@R13
A=M
0;JMP
// label IF_FALSE
(Main.fibonacci$IF_FALSE)
// push argument 0
@0
D=A
@ARG
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push constant 2
@2
D=A
@SP
A=M
M=D
@SP
M=M+1
// sub
@SP
AM=M-1
D=M
A=A-1
M=M-D
// call Main.fibonacci 1
@Main.fibonacci$ret.1
D=A
@SP
A=M
M=D
@SP
M=M+1
@LCL
D=M
@SP
A=M
M=D
@SP
M=M+1
@ARG
D=M
@SP
A=M
M=D
@SP
M=M+1
@THIS
D=M
@SP
A=M
M=D
@SP
M=M+1
@THAT
D=M
@SP
A=M
M=D
@SP
M=M+1
@5
D=A
@1
D=D+A
@SP
D=M-D
@ARG
M=D
@Main.fibonacci
0;JMP
(Main.fibonacci$ret.1)
// push argument 0
@0
D=A
@ARG
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push constant 1
@1
D=A
@SP
A=M
M=D
@SP
M=M+1
// sub
@SP
AM=M-1
D=M
A=A-1
M=M-D
// call Main.fibonacci 1
@Main.fibonacci$ret.2
D=A
@SP
A=M
M=D
@SP
M=M+1
@LCL
D=M
@SP
A=M
M=D
@SP
M=M+1
@ARG
D=M
@SP
A=M
M=D
@SP
M=M+1
@THIS
D=M
@SP
A=M
M=D
@SP
M=M+1
@THAT
D=M
@SP
A=M
M=D
@SP
M=M+1
@5
D=A
@1
D=D+A
@SP
D=M-D
@ARG
M=D
@Main.fibonacci
0;JMP
(Main.fibonacci$ret.2)
// add
@SP
AM=M-1
D=M
A=A-1
M=M+D
// return
@5
D=A
@LCL
A=M-D
D=M
@R13
M=D
@SP
A=M-1
D=M
@ARG
A=M
M=D
@ARG
D=M+1
@SP
M=D
@LCL
AM=M-1
D=M
@THAT
M=D
@LCL
AM=M-1
D=M
@THIS
M=D
@LCL
AM=M-1
D=M
@ARG
M=D
@LCL
AM=M-1
D=M
@LCL
M=D
@R13
A=M
0;JMP
// function Sys.init 0
(Sys.init)
@SP
D=M
@LCL
M=D
@0
D=A
@SP
M=M+D
@Sys.init$lcl_init_ignore
D;JEQ
@R13
M=D
@R14
M=0
(Sys.init$lcl_init)
@R14
D=M
@LCL
A=D+M
M=0
@R14
MD=D+1
@R13
D=D-M
@Sys.init$lcl_init
D;JLT
(Sys.init$lcl_init_ignore)
// push constant 4
@4
D=A
@SP
A=M
M=D
@SP
M=M+1
// call Main.fibonacci 1
@Sys.init$ret.1
D=A
@SP
A=M
M=D
@SP
M=M+1
@LCL
D=M
@SP
A=M
M=D
@SP
M=M+1
@ARG
D=M
@SP
A=M
M=D
@SP
M=M+1
@THIS
D=M
@SP
A=M
M=D
@SP
M=M+1
@THAT
D=M
@SP
A=M
M=D
@SP
M=M+1
@5
D=A
@1
D=D+A
@SP
D=M-D
@ARG
M=D
@Main.fibonacci
0;JMP
(Sys.init$ret.1)
// label WHILE
(Sys.init$WHILE)
// goto WHILE
@Sys.init$WHILE
0;JMP