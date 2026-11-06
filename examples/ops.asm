MOV A, 12
MOV B, 3
CALL multiplicar
OUT 1, C

MOV A, 12
MOV B, 3
CALL dividir
OUT 1, C
OUT 1, A

HLT

multiplicar:
	MOV C, 0
bucle_m:
	CMP B, 0
	JZ fin
	ADD C, A
	SUB B, 1
	JMP bucle_m	
fin:
	RET

dividir:
  MOV C, 0          ; C = Cociente (Contador de restas)

bucle_d:
  CMP A, B          ; Compara Dividendo (A) con Divisor (B)
  JC fin_div        ; Si A < B, no podemos seguir restando (salta)

  SUB A, B          ; Resta el divisor del dividendo (A = A - B)
  ADD C, 1          ; Incrementa el cociente
  JMP bucle_d

fin_div:
  RET