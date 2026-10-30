class Memory:
    def __init__(self, size=256):
        self.size = size
        self.data = [0] * size

    def read(self, address):
        if 0 <= address < self.size:
            return self.data[address]
        return 0

    def write(self, address, value):
        if 0 <= address < self.size:
            self.data[address] = value & 0xFF

    def reset(self):
        self.data = [0] * self.size


class CPU:
    def __init__(self, memory, io_devices=None):
        self.memory = memory
        self.io = io_devices if io_devices else {'in': {}, 'out': {}}
        self.reset()

    def reset(self):
        self.registers = {0: 0, 1: 0, 2: 0, 3: 0} # 0=A, 1=B, 2=C, 3=D
        self.pc = 0
        self.sp = 0xFF 
        self.zero_flag = False
        self.carry_flag = False
        self.halted = False
        self.error = None

    def fetch(self):
        if self.pc >= self.memory.size:
            self.halted = True
            return None
        instruction = self.memory.read(self.pc)
        self.pc += 1
        return instruction

    def update_flags(self, value, carry=False):
        self.zero_flag = ((value & 0xFF) == 0)
        self.carry_flag = carry

    def step(self):
        if self.halted: return "CPU Halted."
        
        byte1 = self.fetch()
        if byte1 is None: return "Fin de memoria."

        opcode = byte1 >> 3
        operand = byte1 & 0x07

        if opcode == 0x00: return f"[{self.pc-1:02X}] NOP"
        elif opcode == 0x01: 
            reg = operand & 0x3
            port = self.fetch()
            val = self.io['in'].get(port, lambda: 0)() & 0xFF
            self.registers[reg] = val
            return f"[{self.pc-2:02X}] IN {self._rname(reg)}, P{port:02X}"
        elif opcode == 0x02: # OUT P, REG / OUT P, $REG
            fmt_ascii = bool(operand & 0x4)
            reg = operand & 0x3
            port = self.fetch()
            val = self.registers[reg]
            if port in self.io['out']: 
                self.io['out'][port](val, is_ascii=fmt_ascii)
            str_reg = f"${self._rname(reg)}" if fmt_ascii else self._rname(reg)
            return f"[{self.pc-2:02X}] OUT P{port:02X}, {str_reg}"
        elif opcode == 0x03:
            self.halted = True
            return f"[{self.pc-1:02X}] HLT"
        elif opcode == 0x04:
            reg = operand & 0x3
            val = self.fetch()
            self.registers[reg] = val
            return f"[{self.pc-2:02X}] MOV {self._rname(reg)}, {val:02X}"
        elif opcode == 0x05:
            dest = operand & 0x3
            src = self.fetch() & 0x3
            self.registers[dest] = self.registers[src]
            return f"[{self.pc-2:02X}] MOV {self._rname(dest)}, {self._rname(src)}"
        elif opcode == 0x06: # ADD con 2 parámetros
            dest = operand & 0x3
            if operand & 0x4: # ADD reg, inm (2 bytes)
                val = self.fetch()
                res = self.registers[dest] + val
                self.registers[dest] = res & 0xFF
                self.update_flags(self.registers[dest], carry=(res > 0xFF))
                return f"[{self.pc-2:02X}] ADD {self._rname(dest)}, {val:02X}"
            else: # ADD reg1, reg2 (2 bytes)
                src = self.fetch() & 0x3
                res = self.registers[dest] + self.registers[src]
                self.registers[dest] = res & 0xFF
                self.update_flags(self.registers[dest], carry=(res > 0xFF))
                return f"[{self.pc-2:02X}] ADD {self._rname(dest)}, {self._rname(src)}"
        elif opcode == 0x07: # SUB reg
            reg = operand & 0x3
            res = self.registers[0] - self.registers[reg] # A - reg
            self.registers[0] = res & 0xFF                # Resultado a A
            self.update_flags(self.registers[0], carry=(res < 0))
            return f"[{self.pc-1:02X}] SUB {self._rname(reg)}"
        elif opcode == 0x08:
            reg = operand & 0x3
            res = (self.registers[reg] << 1)
            self.registers[reg] = res & 0xFF
            self.update_flags(self.registers[reg], carry=(res > 0xFF))
            return f"[{self.pc-1:02X}] SHF {self._rname(reg)}"
        elif opcode == 0x09:
            reg = operand & 0x3
            res = self.registers[0] & self.registers[reg]
            self.registers[0] = res
            self.update_flags(res)
            return f"[{self.pc-1:02X}] AND {self._rname(reg)}"
        elif opcode == 0x0A:
            reg = operand & 0x3
            res = self.registers[0] | self.registers[reg]
            self.registers[0] = res
            self.update_flags(res)
            return f"[{self.pc-1:02X}] OR {self._rname(reg)}"
        elif opcode == 0x0B:
            reg = operand & 0x3
            res = self.registers[0] ^ self.registers[reg]
            self.registers[0] = res
            self.update_flags(res)
            return f"[{self.pc-1:02X}] XOR {self._rname(reg)}"
        elif opcode == 0x0C: # CMP reg
            reg = operand & 0x3
            res = self.registers[0] - self.registers[reg]
            self.update_flags(res & 0xFF, carry=(res < 0))
            return f"[{self.pc-1:02X}] CMP {self._rname(reg)}"
        elif opcode == 0x0D:
            reg = operand & 0x3
            addr = self.fetch()
            self.registers[reg] = self.memory.read(addr)
            return f"[{self.pc-2:02X}] LD {self._rname(reg)}, [{addr:02X}]"
        elif opcode == 0x0E:
            reg = operand & 0x3
            addr = self.fetch()
            self.memory.write(addr, self.registers[reg])
            return f"[{self.pc-2:02X}] ST [{addr:02X}], {self._rname(reg)}"
        elif opcode == 0x0F:
            addr = self.fetch()
            self.pc = addr
            return f"[{self.pc-2:02X}] JMP {addr:02X}"
        elif opcode == 0x10:
            addr = self.fetch()
            if self.zero_flag: self.pc = addr
            return f"[{self.pc-2:02X}] JZ {addr:02X}"
        elif opcode == 0x11:
            addr = self.fetch()
            if not self.zero_flag: self.pc = addr
            return f"[{self.pc-2:02X}] JNZ {addr:02X}"
        elif opcode == 0x12:
            reg = operand & 0x3
            self.memory.write(self.sp, self.registers[reg])
            self.sp = (self.sp - 1) & 0xFF
            return f"[{self.pc-1:02X}] PUSH {self._rname(reg)}"
        elif opcode == 0x13:
            reg = operand & 0x3
            self.sp = (self.sp + 1) & 0xFF
            self.registers[reg] = self.memory.read(self.sp)
            return f"[{self.pc-1:02X}] POP {self._rname(reg)}"
        elif opcode == 0x14:
            target_addr = self.fetch()
            self.memory.write(self.sp, self.pc)
            self.sp = (self.sp - 1) & 0xFF
            self.pc = target_addr
            return f"[{self.pc-2:02X}] CALL {target_addr:02X}"
        elif opcode == 0x15:
            self.sp = (self.sp + 1) & 0xFF
            return_addr = self.memory.read(self.sp)
            self.pc = return_addr
            return f"[{self.pc-1:02X}] RET -> {return_addr:02X}"
        elif opcode == 0x16:
            reg = operand & 0x3
            reg_ptr = self.fetch() & 0x3
            self.registers[reg] = self.memory.read(self.registers[reg_ptr])
            return f"[{self.pc-2:02X}] LDI {self._rname(reg)}, [{self._rname(reg_ptr)}]"
        elif opcode == 0x17:
            reg_ptr = operand & 0x3
            reg = self.fetch() & 0x3
            self.memory.write(self.registers[reg_ptr], self.registers[reg])
            return f"[{self.pc-2:02X}] STI [{self._rname(reg_ptr)}], {self._rname(reg)}"
        elif opcode == 0x18: # CMP reg, inm
            reg = operand & 0x3
            val = self.fetch()
            res = self.registers[reg] - val
            self.update_flags(res & 0xFF, carry=(res < 0))
            return f"[{self.pc-2:02X}] CMP {self._rname(reg)}, {val:02X}"
        elif opcode == 0x19: # DIV reg
            reg = operand & 0x3
            divisor = self.registers[reg]
            if divisor == 0:
                self.halted = True
                self.error = "DIV BY ZERO"
                return f"[{self.pc-1:02X}] ERR: DIV BY ZERO"
            
            dividend = self.registers[0]
            quotient = (dividend // divisor) & 0xFF
            remainder = (dividend % divisor) & 0xFF
            
            self.registers[0] = quotient
            self.registers[2] = remainder
            self.update_flags(quotient)
            return f"[{self.pc-1:02X}] DIV {self._rname(reg)}"

    def _rname(self, code):
        return {0: 'A', 1: 'B', 2: 'C', 3: 'D'}.get(code, 'A')