// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed.
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

// holds current state, 0=white, 1=black
  @state
  M=0

  @16384
  D=A

  @cur
  M=D

  @24576
  D=A

  @end
  M=D

// We poll keyboard as long as the state
// holds
(KBD_POLL)
  @KBD
  D=M

  @WHITE_CHECK
  D;JEQ
  @BLACK_CHECK
  D;JNE

(WHITE_CHECK)
  @state
  D=M

  @KBD_POLL
  D;JEQ

  @WHITEN
  0;JMP


(BLACK_CHECK)
  @state
  D=M

  @KBD_POLL
  D-1;JEQ

  @BLACKEN
  0;JMP

(BLACKEN)
  @state
  M=1

  @filler
  M=-1

  @FILL_SCREEN
  0;JMP


(WHITEN)
  @state
  M=0

  @filler
  M=0

  @FILL_SCREEN
  0;JMP

(FILL_SCREEN)
  @filler
  D=M

  @cur
  A=M // load address row to flood
  M=D

  @cur
  M=M+1
  D=M

  @end
  D=M-D

  @FILL_SCREEN
  D;JNE

  @16384
  D=A

  @cur
  M=D

  @KBD_POLL
  0;JMP
