# Simulador de CPU Modular de 8 Bits con Interfaz GTK4

Un simulador visual e interactivo de una arquitectura de CPU de 8 bits desarrollado en Python con GTK4. Cuenta con un ensamblador integrado con soporte para cadenas y literales ASCII, visualización de memoria codificada por colores, terminal I/O interactiva y ejecutor paso a paso/en tiempo real.

---

## 🛠️ Arquitectura del Sistema

* **Bus de Datos / Registros:** 8 bits ($00 - FF / 0 - 255$).
* **Memoria:** 256 Bytes direccionables ($00 - FF$).
* **Registros de Propósito General:** 4 registros de 8 bits (`A`, `B`, `C`, `D`).
  * `A`: Acumulador por defecto para operaciones aritmético-lógicas y cociente en `DIV`.
  * `C`: Registro auxiliar / almacenamiento de residuo en `DIV`.
* **Punteros Internos:**
  * `PC` (Program Counter): Apunta a la instrucción actual en ejecución.
  * `SP` (Stack Pointer): Inicializado en `0xFF`, decrece con `PUSH`/`CALL` e incrementa con `POP`/`RET`.
* **Flags (Banderas):**
  * `Z` (Zero Flag): Se activa ($1$) si el resultado de una operación es $0$.
  * `C` (Carry Flag): Se activa ($1$) en caso de acarreo/desbordamiento (suma $> 255$ o resta $< 0$).
* **Puertos de I/O:** 256 puertos de entrada/salida ($00 - FF$).
  * **Puerto 0 (Entrada):** Teclado / Búfer de caracteres.
  * **Puerto 1 (Salida):** Terminal de texto (modos entero y ASCII).

---

## 📑 Sintaxis del Ensamblador

El ensamblador admite secciones, etiquetas, literales de carácter y directivas de datos:

* **Secciones:**
  * `.CODE`: Define el bloque de instrucciones ejecutables (empieza en la dirección `0x00`).
  * `.DATA`: Define constantes y cadenas almacenadas en memoria tras el código de usuario.
* **Etiquetas:** Definen saltos o referencias a memoria finalizadas en dos puntos (`ETIQUETA:`).
* **Literales ASCII e Inmediatos:**
  * Enteros Decimales: `10`, `255`
  * Enteros Hexadecimales: `0x0A`, `0xFF`
  * Caracteres ASCII explícitos: `$'a'`, `$','`, `$' '`
* **Directiva `.DATA`:**
  * `DB "Hola Mundo", 0`: Almacena una cadena terminada en nulo ($0x00$).
  * `DB 10, 20, 0x30`: Almacena valores numéricos consecutivos.

---

## 📊 Tabla de Opcodes e Instrucciones

Los opcodes ocupan los 5 bits más significativos del primer byte (`opcode = byte >> 3`), mientras que los 3 bits menos significativos especifican el registro o modo (`operand = byte & 0x07`).

| Mnemónico | Opcode (Hex) | Tamaño | Descripción / Operación | Banderas Afectadas |
| :--- | :---: | :---: | :--- | :---: |
| **`NOP`** | `0x00` | 1 Byte | Sin operación. | Ninguna |
| **`IN reg, port`** | `0x01` | 2 Bytes | Lee el valor del puerto I/O en `reg`. | Ninguna |
| **`OUT port, reg`** | `0x02` | 2 Bytes | Muestra el valor de `reg` en `port` (Formato Numérico). | Ninguna |
| **`OUT port, $reg`**| `0x02` | 2 Bytes | Muestra el valor de `reg` en `port` (Formato Carácter ASCII). | Ninguna |
| **`HLT`** | `0x03` | 1 Byte | Detiene la ejecución de la CPU. | Ninguna |
| **`MOV reg, inm`** | `0x04` | 2 Bytes | Carga el valor inmediato `inm` en `reg`. | Ninguna |
| **`MOV dest, src`** | `0x05` | 2 Bytes | Copia el contenido de `src` en `dest`. | Ninguna |
| **`ADD reg`** | `0x06` | 1 Byte | `A = A + reg` | Z, C |
| **`SUB reg`** | `0x07` | 1 Byte | `A = A - reg` | Z, C |
| **`SHF reg`** | `0x08` | 1 Byte | Desplazamiento a la izquierda: `reg = reg << 1` | Z, C |
| **`AND reg`** | `0x09` | 1 Byte | `A = A & reg` (AND bit a bit) | Z |
| **`OR reg`** | `0x0A` | 1 Byte | `A = A \| reg` (OR bit a bit) | Z |
| **`XOR reg`** | `0x0B` | 1 Byte | `A = A ^ reg` (XOR bit a bit) | Z |
| **`CMP reg`** | `0x0C` | 1 Byte | Compara `A` con `reg` (Resta interna `A - reg`). | Z, C |
| **`CMP reg, inm`** | `0x18` | 2 Bytes | Compara `reg` con `inm` (Resta interna `reg - inm`). | Z, C |
| **`LD reg, [addr]`**| `0x0D` | 2 Bytes | Carga en `reg` el contenido de la dirección `addr`. | Ninguna |
| **`ST [addr], reg`**| `0x0E` | 2 Bytes | Almacena el contenido de `reg` en la dirección `addr`. | Ninguna |
| **`JMP addr`** | `0x0F` | 2 Bytes | Salto incondicional a `addr`. | Ninguna |
| **`JZ addr`** | `0x10` | 2 Bytes | Salta a `addr` si `Z == 1`. | Ninguna |
| **`JNZ addr`** | `0x11` | 2 Bytes | Salta a `addr` si `Z == 0`. | Ninguna |
| **`PUSH reg`** | `0x12` | 1 Byte | Guarda `reg` en la Pila (`mem[SP] = reg; SP--`). | Ninguna |
| **`POP reg`** | `0x13` | 1 Byte | Recupera de la Pila a `reg` (`SP++; reg = mem[SP]`). | Ninguna |
| **`CALL addr`** | `0x14` | 2 Bytes | Llama a subrutina en `addr` (Apila `PC` de retorno). | Ninguna |
| **`RET`** | `0x15` | 1 Byte | Retorna de subrutina (Desapila dirección hacia `PC`). | Ninguna |
| **`LDI dest, [ptr]`**| `0x16`| 2 Bytes | Carga indirecta: `dest = mem[ptr]`. | Ninguna |
| **`STI [ptr], src`**| `0x17` | 2 Bytes | Almacenamiento indirecto: `mem[ptr] = src`. | Ninguna |
| **`DIV reg`** | `0x19` | 1 Byte | Divide `A / reg`. Cociente $\rightarrow$ `A`, Residuo $\rightarrow$ `C`. | Z |

---

## 🎯 Codificación de Registros

| Registro | Identificador Binario | Valor Numérico |
| :---: | :---: | :---: |
| **`A`** | `00` | 0 |
| **`B`** | `01` | 1 |
| **`C`** | `10` | 2 |
| **`D`** | `11` | 3 |

---

## 💻 Ejemplo: Generación de Fibonacci con Texto (.DATA)

El siguiente programa imprime una cadena de texto desde memoria y calcula la serie de Fibonacci hasta desbordar los 8 bits ($>255$):

```assembly
; --- SERIE DE FIBONACCI CON SALIDA FORMATEADA ---
.CODE
  ; 1. Imprimir mensaje inicial desde .DATA
  MOV A, msj_inicio
  CALL PRINT_STR

  ; 2. Inicializar secuencia
  MOV A, 0
  MOV B, 1

BUCLE:
  OUT 1, A          ; Imprimir valor entero de A
  MOV C, $','
  OUT 1, $C         ; Imprimir coma ASCII
  MOV C, $' '
  OUT 1, $C         ; Imprimir espacio ASCII

  MOV C, A
  ADD B             ; A = A + B
  JZ FIN            ; Salir si es cero por rollover
  JC FIN            ; Salir si hay acarreo (> 255)

  MOV B, C          ; Avanzar pareja
  JMP BUCLE

FIN:
  MOV C, $'.'
  OUT 1, $C         ; Imprimir punto final
  HLT

; Subrutina para imprimir cadenas terminadas en 0
PRINT_STR:
  MOV B, A
BUCLE_PRINT:
  LDI C, B          ; C = memoria[B]
  CMP C, 0          ; ¿Fin de cadena?
  JZ FIN_PRINT
  OUT 1, $C         ; Imprimir carácter en ASCII
  MOV A, B
  MOV D, 1
  ADD D             ; Incrementar puntero (B = B + 1)
  MOV B, A
  JMP BUCLE_PRINT
FIN_PRINT:
  RET

.DATA
msj_inicio: DB "Fibonacci: ", 0
```

---

## 🚀 Instalación y Ejecución

### Requisitos Previos (Ubuntu/Debian/Arch)
Asegúrate de contar con Python 3 y las dependencias de GTK4 e PyGObject:

```bash
# Ubuntu / Debian
sudo apt install python3-gi python3-gi-cairo libgtk-4-dev

# Arch Linux
sudo pacman -S python-gobject gtk4
```

### Estructura de Ficheros
```text
pycpu2/
├── main.py
├── ui.py
├── cpu.py
├── assembler.py
├── window.ui (opcional)
└── README.md
```

### Ejecutar la Aplicación
```bash
python3 main.py
```