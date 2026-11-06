# 🖥️ Simulador de CPU de 8 bits (GTK4 & Web Debugger)

Un simulador pedagógico de una CPU de 8 bits con soporte para un juego de instrucciones (ISA) de 1 y 2 bytes, ensamblador integrado, mapa de memoria visual, traza de ejecución y control de entrada/salida (I/O).

---

## 📑 Tabla de Contenidos

* [Arquitectura General](https://www.google.com/search?q=%23-arquitectura-general)
* [Mapa de Registros y Memoria](https://www.google.com/search?q=%23-mapa-de-registros-y-memoria)
* [Juego de Instrucciones (ISA) y Opcodes](https://www.google.com/search?q=%23-juego-de-instrucciones-isa-y-opcodes)
* [Modos de Direccionamiento](https://www.google.com/search?q=%23-modos-de-direccionamiento)
* [Sistema de Periféricos (I/O)](https://www.google.com/search?q=%23-sistema-de-perif%C3%A9ricos-io)
* [Instalación y Ejecución](https://www.google.com/search?q=%23-instalaci%C3%B3n-y-ejecuci%C3%B3n)
* [Ejemplos de Programación](https://www.google.com/search?q=%23-ejemplos-de-programaci%C3%B3n)

---

## 🏗️ Arquitectura General

* **Tamaño de Palabra**: 8 bits ($0x00$ a $0xFF$, valores enteros de $0$ a $255$).
* **Memoria RAM**: 256 Bytes direccionables ($0x00$ a $0xFF$).
* **Registros de Propósito General**: `A`, `B`, `C`, `D` (8 bits cada uno).
* **Punteros Internos**:
* `PC` (Program Counter): Señala la dirección de la siguiente instrucción a ejecutar.
* `SP` (Stack Pointer): Apunta a la cima de la pila en memoria (inicializado en $0xFF$).


* **Banderas de Estado (Flags)**:
* **$Z$ (Zero Flag)**: Se activa ($1$) cuando el resultado de una operación es $0$.
* **$C$ (Carry Flag / Borrow)**: Se activa ($1$) cuando una suma desborda los 8 bits ($>255$) o cuando una resta/comparación requiere un préstamo ($dest < src$).



---

## 💾 Mapa de Registros y Memoria

### Codificación de Registros (2 bits)

| Nombre | Código Binario | Código Hex |
| --- | --- | --- |
| **A** | `00` | `0x00` |
| **B** | `01` | `0x01` |
| **C** | `10` | `0x02` |
| **D** | `11` | `0x03` |

### Organización de Memoria (256 Bytes)

```
+------------------+ 0x00
|     .CODE        |  Sección de instrucciones executables (crece hacia abajo)
|                  |
+------------------+
|     .DATA        |  Variables y cadenas declaradas con DB
|                  |
+------------------+
|        ...       |  Espacio libre
+------------------+
|     STACK        |  Pila (crece hacia abajo desde 0xFF)
+------------------+ 0xFF

```

---

## ⚙️ Juego de Instrucciones (ISA) y Opcodes

Las instrucciones pueden ser de **1 Byte** (Opcode + Registro) o **2 Bytes** (Opcode + Registro + Valor Inmediato/Dirección/Segundo Registro).

| Mnemónico | Sintaxis | Bytes | Opcode (Hex) | Descripción | Banderas Afectadas |
| --- | --- | --- | --- | --- | --- |
| **NOP** | `NOP` | 1 | `0x00` | Sin operación. | Ninguna |
| **IN** | `IN reg, puerto` | 2 | `0x08 | reg` | Lee un byte del puerto I/O al registro. | Ninguna |
| **OUT** | `OUT puerto, reg` | 2 | `0x10 | reg` | Imprime el número del registro en el puerto I/O. | Ninguna |
|  | `OUT puerto, $reg` | 2 | `0x14 | reg` | Imprime el carácter ASCII del registro en el puerto. | Ninguna |
| **HLT** | `HLT` | 1 | `0x18` | Detiene la ejecución de la CPU. | Ninguna |
| **MOV** | `MOV dest, inm` | 2 | `0x20 | dest` | Carga valor inmediato en el registro destino. | Ninguna |
|  | `MOV dest, src` | 2 | `0x28 | dest` | Copia el contenido de `src` en `dest`. | Ninguna |
| **ADD** | `ADD dest, src` | 2 | `0x30 | dest` | `dest = dest + src`. | $Z$, $C$ |
|  | `ADD dest, inm` | 2 | `0x34 | dest` | `dest = dest + inm`. | $Z$, $C$ |
| **SUB** | `SUB dest, src` | 2 | `0x38 | dest` | `dest = dest - src`. | $Z$, $C$ |
|  | `SUB dest, inm` | 2 | `0x3C | dest` | `dest = dest - inm`. | $Z$, $C$ |
| **MUL** | `MUL dest, src` | 2 | `0xD0 | dest` | `dest = dest * src`. | $Z$, $C$ |
|  | `MUL dest, inm` | 2 | `0xD4 | dest` | `dest = dest * inm`. | $Z$, $C$ |
| **DIV** | `DIV dest, src` | 2 | `0xE0 | dest` | `dest = dest // src` (división entera). | $Z$ |
|  | `DIV dest, inm` | 2 | `0xE4 | dest` | `dest = dest // inm`. | $Z$ |
| **SHF** | `SHF reg` | 1 | `0x40 | reg` | Desplazamiento a la izquierda (`reg << 1`). | $Z$, $C$ |
| **AND** | `AND reg` | 1 | `0x48 | reg` | Operación lógica: `A = A & reg`. | $Z$ |
| **OR** | `OR reg` | 1 | `0x50 | reg` | Operación lógica: `A = A | reg`. | $Z$ |
| **XOR** | `XOR reg` | 1 | `0x58 | reg` | Operación lógica: `A = A ^ reg`. | $Z$ |
| **CMP** | `CMP A, reg` / `CMP reg` | 1 | `0x60 | reg` | Compara `A` con `reg` (resta interna `A - reg`). | $Z$, $C$ |
|  | `CMP reg, inm` | 2 | `0xC0 | reg` | Compara `reg` con valor inmediato (`reg - inm`). | $Z$, $C$ |
| **LD** | `LD reg, [addr]` | 2 | `0x68 | reg` | Carga en `reg` el valor de la memoria `[addr]`. | Ninguna |
| **ST** | `ST [addr], reg` | 2 | `0x70 | reg` | Almacena `reg` en la dirección `[addr]`. | Ninguna |
| **LDI** | `LDI reg, [ptr]` | 2 | `0xB0 | reg` | Carga en `reg` usando direccionamiento indirecto por registro `[ptr]`. | Ninguna |
| **STI** | `STI [ptr], reg` | 2 | `0xB8 | ptr` | Almacena `reg` en la dirección contenida en `[ptr]`. | Ninguna |
| **JMP** | `JMP addr` | 2 | `0x78` | Salto incondicional a `addr`. | Ninguna |
| **JZ** | `JZ addr` | 2 | `0x80` | Salto condicional a `addr` si $Z = 1$. | Ninguna |
| **JNZ** | `JNZ addr` | 2 | `0x88` | Salto condicional a `addr` si $Z = 0$. | Ninguna |
| **JC** | `JC addr` | 2 | `0xC8` | Salto condicional a `addr` si $C = 1$ (Carry/Borrow). | Ninguna |
| **PUSH** | `PUSH reg` | 1 | `0x90 | reg` | Guarda el contenido de `reg` en la pila. | Ninguna |
| **POP** | `POP reg` | 1 | `0x98 | reg` | Recupera el valor de la cima de la pila a `reg`. | Ninguna |
| **CALL** | `CALL addr` | 2 | `0xA0` | Llama a subrutina (guarda dirección de retorno en la pila). | Ninguna |
| **RET** | `RET` | 1 | `0xA8` | Retorna de subrutina (restaura el `PC` desde la pila). | Ninguna |

---

## 🎯 Modos de Direccionamiento

1. **Inmediato**: El operando es una constante numérica o carácter.
* Ejemplos: `MOV A, 10`, `ADD B, 0x05`, `MOV C, $'A'`


2. **Registro**: La operación se realiza entre registros de la CPU.
* Ejemplos: `MOV A, B`, `ADD C, D`, `SUB A, B`


3. **Directo de Memoria**: Especifica una dirección absoluta en la RAM.
* Ejemplos: `LD A, [0x80]`, `ST [0x40], B`


4. **Indirecto por Registro**: La dirección de memoria está guardada dentro de un registro.
* Ejemplos: `LDI C, [B]`, `STI [B], A`



---

## 🔌 Sistema de Periféricos (I/O)

La CPU utiliza instrucciones dedicadas `IN` y `OUT` para comunicarse con puertos virtuales:

* **Puerto `0` (Entrada/Teclado)**: Permite la lectura de caracteres ingresados desde la interfaz.
* **Puerto `1` (Salida/Pantalla)**:
* `OUT 1, reg`: Muestra el entero decimal directamente en la consola (ej. `36`).
* `OUT 1, $reg`: Interpreta el byte como carácter ASCII (ej. `$'A'` $\rightarrow$ `A`).



---

## 🚀 Instalación y Ejecución

### Versión Escritorio (Python + GTK4)

Requisitos: Python 3.10+, GTK4 y PyGObject.

```bash
# Ejecutar la aplicación
python main.py

```

### Versión Web (HTML5 + JavaScript)

Abre el archivo `index.html` en cualquier navegador web moderno (no requiere dependencias ni servidor Web).

---

## 📝 Ejemplos de Programación

### 1. Divisíon por Restas Sucesivas (con resto y cociente)

```assembly
; --- DIVISIÓN: 38 / 5 ---
.CODE
  MOV A, 38         ; Dividendo
  MOV B, 5          ; Divisor
  CALL dividir
  OUT 1, C          ; Muestra Cociente (7)
  OUT 1, A          ; Muestra Resto (3)
  HLT

dividir:
  MOV C, 0          ; Cociente (Contador)
bucle_d:
  MOV D, A          ; Copia dividendo actual
  SUB D, B          ; Resta de prueba
  JC fin_div        ; Si A < B, activa Carry y salta a fin

  SUB A, B          ; Resta real
  ADD C, 1          ; Incrementar cociente
  JMP bucle_d
fin_div:
  RET

```

### 2. Cadena de Texto en ASCII

```assembly
.CODE
  MOV A, mensaje
  CALL PRINT_STR
  HLT

PRINT_STR:
  MOV B, A
BUCLE:
  LDI C, [B]
  CMP C, 0
  JZ FIN
  OUT 1, $C
  ADD B, 1
  JMP BUCLE
FIN:
  RET

.DATA
mensaje: DB "Hola Mundo!", 0

```
