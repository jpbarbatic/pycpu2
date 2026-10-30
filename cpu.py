import re

class Assembler:
    REGISTERS = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    INSTR_SIZES = {
        'NOP': 1, 'HLT': 1, 'RET': 1, 'DIV': 1,
        'SHF': 1, 'AND': 1, 'OR': 1, 'XOR': 1,
        'PUSH': 1, 'POP': 1,
        'IN': 2, 'OUT': 2, 'LD': 2, 'ST': 2, 'LDI': 2, 'STI': 2,
        'JMP': 2, 'JZ': 2, 'JNZ': 2, 'CALL': 2, 'ADD': 2, 'SUB': 2
    }

    @classmethod
    def tokenize(cls, line_str):
        line_clean = line_str.split(';')[0].strip()
        if not line_clean:
            return []

        tokens = []
        i = 0
        n = len(line_clean)

        while i < n:
            if line_clean[i] in ' \t,[]':
                i += 1
                continue

            if line_clean[i:i+2] == "$'" and i + 3 < n and line_clean[i+3] == "'":
                tokens.append(line_clean[i:i+4])
                i += 4
                continue

            if line_clean[i] == '"':
                end = line_clean.find('"', i + 1)
                if end != -1:
                    tokens.append(line_clean[i:end+1])
                    i = end + 1
                    continue

            start = i
            while i < n and line_clean[i] not in ' \t,[]"':
                i += 1
            tokens.append(line_clean[start:i])

        return tokens

    @classmethod
    def assemble(cls, code):
        labels = {}
        memory_map = {} 
        address_to_line = {}
        lines = code.split('\n')
        
        try:
            code_size = 0
            in_code_section = True
            
            for line in lines:
                tokens = cls.tokenize(line)
                if not tokens: continue
                
                first_token_upper = tokens[0].upper()
                if first_token_upper == '.CODE': 
                    in_code_section = True; continue
                elif first_token_upper == '.DATA': 
                    in_code_section = False; continue
                
                if in_code_section:
                    if tokens[0].endswith(':'):
                        tokens = tokens[1:]
                        if not tokens: continue
                    
                    instr = tokens[0].upper()
                    if instr == 'MOV': 
                        code_size += 2
                    elif instr == 'ADD' or instr == 'SUB':
                        code_size += 2
                    elif instr == 'CMP':
                        code_size += 2 if len(tokens) == 3 else 1
                    elif instr in cls.INSTR_SIZES: 
                        code_size += cls.INSTR_SIZES[instr]

            code_addr = 0x00
            data_addr = code_size
            current_section = '.CODE'
            parsed_instructions = []

            for line_idx, raw_line in enumerate(lines):
                tokens = cls.tokenize(raw_line)
                if not tokens: continue

                first_token_upper = tokens[0].upper()
                if first_token_upper == '.DATA': current_section = '.DATA'; continue
                elif first_token_upper == '.CODE': current_section = '.CODE'; continue

                if tokens[0].endswith(':'):
                    label_name = tokens[0][:-1].strip().upper()
                    labels[label_name] = data_addr if current_section == '.DATA' else code_addr
                    tokens = tokens[1:]
                    if not tokens: continue

                if current_section == '.DATA':
                    if tokens[0].upper() == 'DB':
                        string_match = re.search(r'"([^"]*)"', raw_line)
                        if string_match:
                            text = string_match.group(1)
                            for char in text:
                                memory_map[data_addr] = ord(char)
                                data_addr += 1
                            memory_map[data_addr] = 0x00 
                            data_addr += 1
                        else:
                            for v in tokens[1:]:
                                val = int(v, 16) if v.upper().startswith('0X') else int(v)
                                memory_map[data_addr] = val & 0xFF
                                data_addr += 1
                
                elif current_section == '.CODE':
                    address_to_line[code_addr] = line_idx
                    parsed_instructions.append((code_addr, tokens))
                    instr = tokens[0].upper()
                    
                    if instr == 'MOV': 
                        code_addr += 2 
                    elif instr == 'ADD' or instr == 'SUB':
                        code_addr += 2
                    elif instr == 'CMP':
                        code_addr += 2 if len(tokens) == 3 else 1
                    elif instr in cls.INSTR_SIZES: 
                        code_addr += cls.INSTR_SIZES[instr]

            def resolve_val(v):
                v_clean = v.strip()
                if v_clean.startswith("$'") and v_clean.endswith("'") and len(v_clean) == 4:
                    return ord(v_clean[2])
                
                v_upper = v_clean.upper()
                if v_upper in labels:
                    return labels[v_upper]
                if v_upper.startswith('0X'):
                    return int(v_upper, 16)
                
                return int(v_upper)

            for addr, parts in parsed_instructions:
                instr = parts[0].upper()

                if instr == 'NOP': memory_map[addr] = 0x00
                elif instr == 'IN':
                    memory_map[addr] = 0x08 | cls.REGISTERS[parts[1].upper()]
                    memory_map[addr+1] = resolve_val(parts[2]) & 0xFF
                elif instr == 'OUT':
                    port_val = resolve_val(parts[1]) & 0xFF
                    reg_str = parts[2].upper()
                    if reg_str.startswith('$'):
                        fmt_flag = 1
                        reg_name = reg_str[1:]
                    else:
                        fmt_flag = 0
                        reg_name = reg_str
                    memory_map[addr] = 0x10 | (fmt_flag << 2) | cls.REGISTERS[reg_name]
                    memory_map[addr+1] = port_val
                elif instr == 'HLT': memory_map[addr] = 0x18
                elif instr == 'MOV':
                    dest, src = parts[1].upper(), parts[2]
                    src_upper = src.upper()
                    if src_upper in cls.REGISTERS:
                        memory_map[addr] = 0x28 | cls.REGISTERS[dest]
                        memory_map[addr+1] = cls.REGISTERS[src_upper]
                    else:
                        memory_map[addr] = 0x20 | cls.REGISTERS[dest]
                        memory_map[addr+1] = resolve_val(src) & 0xFF
                elif instr == 'ADD':
                    dest = parts[1].upper()
                    src_or_imm = parts[2]
                    src_upper = src_or_imm.upper()

                    if src_upper in cls.REGISTERS:
                        memory_map[addr] = 0x30 | cls.REGISTERS[dest]
                        memory_map[addr+1] = cls.REGISTERS[src_upper]
                    else:
                        memory_map[addr] = 0x34 | cls.REGISTERS[dest]
                        memory_map[addr+1] = resolve_val(src_or_imm) & 0xFF
                elif instr == 'SUB':
                    dest = parts[1].upper()
                    src_or_imm = parts[2]
                    src_upper = src_or_imm.upper()

                    if src_upper in cls.REGISTERS:
                        memory_map[addr] = 0x38 | cls.REGISTERS[dest]
                        memory_map[addr+1] = cls.REGISTERS[src_upper]
                    else:
                        memory_map[addr] = 0x3C | cls.REGISTERS[dest]
                        memory_map[addr+1] = resolve_val(src_or_imm) & 0xFF
                elif instr == 'SHF': memory_map[addr] = 0x40 | cls.REGISTERS[parts[1].upper()]
                elif instr == 'AND': memory_map[addr] = 0x48 | cls.REGISTERS[parts[1].upper()]
                elif instr == 'OR':  memory_map[addr] = 0x50 | cls.REGISTERS[parts[1].upper()]
                elif instr == 'XOR': memory_map[addr] = 0x58 | cls.REGISTERS[parts[1].upper()]
                elif instr == 'CMP':
                    if len(parts) == 3:
                        memory_map[addr] = 0xC0 | cls.REGISTERS[parts[1].upper()]
                        memory_map[addr+1] = resolve_val(parts[2]) & 0xFF
                    else:
                        memory_map[addr] = 0x60 | cls.REGISTERS[parts[1].upper()]
                elif instr == 'LD':
                    memory_map[addr] = 0x68 | cls.REGISTERS[parts[1].upper()]
                    memory_map[addr+1] = resolve_val(parts[2]) & 0xFF
                elif instr == 'ST':
                    memory_map[addr] = 0x70 | cls.REGISTERS[parts[2].upper()]
                    memory_map[addr+1] = resolve_val(parts[1]) & 0xFF
                elif instr == 'JMP':
                    memory_map[addr] = 0x78
                    memory_map[addr+1] = resolve_val(parts[1]) & 0xFF
                elif instr == 'JZ':
                    memory_map[addr] = 0x80
                    memory_map[addr+1] = resolve_val(parts[1]) & 0xFF
                elif instr == 'JNZ':
                    memory_map[addr] = 0x88
                    memory_map[addr+1] = resolve_val(parts[1]) & 0xFF
                elif instr == 'PUSH': memory_map[addr] = 0x90 | cls.REGISTERS[parts[1].upper()]
                elif instr == 'POP':  memory_map[addr] = 0x98 | cls.REGISTERS[parts[1].upper()]
                elif instr == 'CALL':
                    memory_map[addr] = 0xA0
                    memory_map[addr+1] = resolve_val(parts[1]) & 0xFF
                elif instr == 'RET': memory_map[addr] = 0xA8
                elif instr == 'LDI':
                    memory_map[addr] = 0xB0 | cls.REGISTERS[parts[1].upper()] 
                    memory_map[addr+1] = cls.REGISTERS[parts[2].upper()]
                elif instr == 'STI':
                    memory_map[addr] = 0xB8 | cls.REGISTERS[parts[1].upper()] 
                    memory_map[addr+1] = cls.REGISTERS[parts[2].upper()]
                elif instr == 'DIV': memory_map[addr] = 0xC8 | cls.REGISTERS[parts[1].upper()]

            return memory_map, address_to_line, code_size, data_addr, None
        except Exception as e:
            return None, None, 0, 0, str(e)