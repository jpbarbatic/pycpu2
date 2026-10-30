; --- SERIE DE FIBONACCI CON SALIDA FORMATEADA ---
.CODE
  ; 1. Imprimir mensaje inicial desde .DATA
  MOV A, msj_inicio
  CALL PRINT_STR

  ; 2. Inicializar términos: A = 0, B = 1
  MOV A, 0
  MOV B, 1

BUCLE:
  ; 3. Imprimir entero actual
  OUT 1, A

  ; 4. Formato visual: coma y espacio en ASCII
  MOV C, $','
  OUT 1, $C
  MOV C, $' '
  OUT 1, $C

  ; 5. Calcular siguiente término (A = A + B)
  MOV C, A
  ADD B

  ; 6. Control de parada por desbordamiento de 8 bits (>255)
  JZ FIN
  JC FIN

  ; 7. Avanzar pareja (B = A anterior)
  MOV B, C
  JMP BUCLE

FIN:
  ; 8. Imprimir punto final y detener
  MOV C, $'.'
  OUT 1, $C
  HLT

; =========================================================
; SUBRUTINA: PRINT_STR
; Imprime caracteres ASCII desde memoria hasta hallar byte 0
; =========================================================
PRINT_STR:
  MOV B, A          ; B = Dirección actual (puntero)

BUCLE_PRINT:
  LDI C, B          ; C = memoria[B]
  CMP C, 0          ; ¿Fin de cadena?
  JZ FIN_PRINT

  OUT 1, $C         ; Imprimir carácter en formato ASCII

  ; Incrementar puntero (B = B + 1)
  MOV A, B
  MOV D, 1
  ADD D
  MOV B, A

  JMP BUCLE_PRINT

FIN_PRINT:
  RET

.DATA
msj_inicio: DB "Fibonacci: ", 0
