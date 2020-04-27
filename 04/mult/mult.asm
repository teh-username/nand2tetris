// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// Put your code here.
// We do repetitive addition
  // Zero checks
  @R0
  D=M
  @ZERO
  D;JEQ

  @R1
  D=M
  @ZERO
  D;JEQ

  @COMPUTE
  0;JMP

(ZERO)
  @R2
  M=0
  @END
  0;JMP

(COMPUTE)
  @iter // iter = 0; counts how many times we've looped
  M=0

  @R2 // R2 = 0; accumulated val
  M=0

(LOOP)
  @R2
  D=M

  @R0
  D=D+M

  @R2
  M=D

  @iter
  M=M+1

  @R1
  D=M

  @iter
  D=D-M // R1 - iter

  @LOOP
  D;JNE // if R1-iter != 0, loop back

(END)
  @END
  0;JMP
