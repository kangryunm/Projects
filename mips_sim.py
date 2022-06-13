import sys
import math

opcode_dict = {
                '001000': 'addi', '001001':  'addiu', '001010': 'slti', '001011': 'sltiu',
                '001100': 'andi', '001101': 'ori', '001110': 'xori', '001111': 'lui',
                '100000': 'lb', '100001': 'lh', '100011': 'lw', '100100': 'lbu', '100101': 'lhu',
                '101000': 'sb', '101001': 'sh', '101011': 'sw',
                '000010': 'j', '000011': 'jal', '000100': 'beq', '000101': 'bne'
                }

R_type_function_fields = {
                        '100000': 'add', '100001': 'addu', '100010': 'sub', '100011': 'subu',
                        '100100': 'and', '100101': 'or', '100110': 'xor', '100111': 'nor',
                        '010000': 'mfhi', '010001': 'mthi', '010010': 'mflo', '010011': 'mtlo',
                        '011000': 'mult', '011001': 'multu', '011010': 'div', '011011': 'divu',
                        '001000': 'jr', '001001': 'jalr', '101010': 'slt', '101011': 'sltu',
                        '000000': 'sll', '000010': 'srl', '000011': 'sra',
                        '000100': 'sllv', '000110': 'srlv', '000111': 'srav'
                        }

registers = {
            0: '0x00000000', 1: '0x00000000', 2: '0x00000000', 3: '0x00000000', 4: '0x00000000',
            5: '0x00000000', 6: '0x00000000', 7: '0x00000000', 8: '0x00000000', 9: '0x00000000',
            10: '0x00000000', 11: '0x00000000', 12: '0x00000000', 13: '0x00000000', 14: '0x00000000',
            15: '0x00000000', 16: '0x00000000', 17: '0x00000000', 18: '0x00000000', 19: '0x00000000',
            20: '0x00000000', 21: '0x00000000', 22: '0x00000000', 23: '0x00000000', 24: '0x00000000',
            25: '0x00000000', 26: '0x00000000', 27: '0x00000000', 28: '0x00000000', 29: '0x00000000',
            30: '0x00000000', 31: '0x00000000'
            }

inst_mem = ['0xFF'] * (16*16*16*16)
data_mem = ['FFFFFFFF'] * (16*16*16*16)

PC = 0

cache1 = [['x' for x in range(32)] for y in range(256)]  # tag(32)
cache2 = [[['0' for k in range(43)] for j in range(2)] for i in range(512)] # V(1) D(1) tag(32) LRU(1) Data Address(8)

def machine_code_2_assembly(cache_type, block_size, inst_num, inst_file, data_file):

    inst_no = 1
    iter1 = 0
    iter2 = 0
    global PC
    global inst_mem
    global data_mem
    global cache1
    global cache2
    hits = 0
    misses = 0

    block_size = int(block_size)
    cache_blocks = int(math.log2(block_size))


    if cache_type == '1':
        cache_sets = int(math.log2(1024/block_size))
    elif cache_type == '2':
        cache_sets = int(math.log2(2048/block_size))

    cache_tag_size = 32 - (cache_sets + cache_blocks)


    with open(inst_file, 'rb') as inst_f:

        iterations = 0
        while True:

            read_by_8 = inst_f.read(4)
            if not read_by_8:
                break

            iterations += 1
            string = read_by_8.hex()
            str_list = []
            str_list.append(string)
            inst_mem[iterations-1] = string

        while True:

            if inst_no > int(inst_num):
                break

            s1 = inst_mem[PC//4]
            s = bin(int(s1, 16))[2:].zfill(32)  # hex to bin

            opcode = s[0:6]
            rs = s[6:11]
            rt = s[11:16]
            rd = s[16:21]
            rs_dec = int(rs, 2)
            rt_dec = int(rt ,2)
            rd_dec = int(rd, 2)
            shamt = s[21:26]  # for R-format
            funct = s[26:32]  # for R-format
            immediate = s[16:32]  # for I-format
            target = s[6:32]  # for J-format


            ## R-type instructions ##
            if opcode == '000000':

                PC += 4
                inst_no += 1

                # not in dict
                if funct not in R_type_function_fields:
                    #print("unknown instruction")
                    break

                # add, addu, and, or,
                # slt, sltu, sub, subu / rd, rs, rt
                if funct[0:3] == '100' or funct[0:3] == '101':
                    rs_temp = int(registers[rs_dec][2:], 16)
                    rt_temp = int(registers[rt_dec][2:], 16)

                    # add / addu
                    if funct == '100000' or funct == '100001':
                        temp = hex(rs_temp + rt_temp)
                        registers[rd_dec] = '0x' + temp[2:].zfill(8)

                    # slt / sltu
                    elif funct == '101010' or funct == '101011':
                        registers[rd_dec] = '0x00000001' if rs_temp < rt_temp else '0x00000000'

                    # and
                    elif funct == '100100':
                        temp = hex(rs_temp | rt_temp)
                        registers[rt_dec] = '0x' + temp[2:].zfill(8)

                    # or
                    elif funct == '100101':
                        temp = hex(rs_temp | rt_temp)
                        registers[rd_dec] = '0x' + temp[2:].zfill(8)

                    # sub / subu
                    elif funct == '100010' or funct == '100011':
                        temp = hex(rs_temp - rt_temp)
                        registers[rd_dec] = '0x' + temp[2:].zfill(8)


                # sll, srl / rd, rt, sa
                elif funct[0:4] == '0000':

                    # sll
                    if funct  == '000000':
                        temp = bin(int(registers[rt_dec][2:], 16))[2:]
                        temp = (int(temp, 2) << int(shamt, 2)) & 0xffffffff
                        registers[rd_dec] = '0x' + hex(temp)[2:].zfill(8)

                    # srl
                    elif funct == '000010':
                        temp = bin(int(registers[rt_dec][2:], 16))[2:]
                        temp = (int(temp, 2) >> int(shamt, 2)) & 0xffffffff
                        registers[rd_dec] = '0x' + hex(temp)[2:].zfill(8)

                # jr / rs
                elif funct == '001000':
                    PC = int(registers[rs_dec][2:], 16)


                else:
                    print("error in R-type")

                continue

            if opcode not in opcode_dict:
                #print("unknown instruction")
                inst_no += 1
                PC += 4
                break


            # I-type instructions
            # addi, addiu, andi, ori, slt, sltiu, (xori)
            if opcode[0:3] == '001' and opcode != '001111':
                rt_dec = int(rt, 2)
                rs_dec = int(rs, 2)

                PC += 4
                inst_no += 1
                imm = 0

                # addi
                #if opcode == '001000':
                if int(immediate[0]) == 1:
                    list(immediate)
                    imm_comp = ''
                    for char in immediate:
                        if char == '1':
                            imm_comp += '0'
                        else:
                            imm_comp += '1'
                    imm = -(int(imm_comp, 2) + 1)


                else:
                    imm = int(immediate, 2)

                # addiu / addi
                if opcode == '001001' or opcode == '001000':
                    if int(immediate[0]) == 1:
                        list(immediate)
                        imm_comp = ''
                        for char in immediate:
                            if char == '1':
                                imm_comp += '0'
                            else:
                                imm_comp += '1'
                        imm = -(int(imm_comp, 2) + 1)

                    else:
                        imm = int(immediate, 2)

                    temp = hex(int(registers[rs_dec][2:], 16) + imm)
                    registers[rt_dec] = '0x' + temp[2:].zfill(8)

                # ori
                elif opcode == '001101':
                    rs_temp = int(registers[rs_dec][2:], 16)
                    result = rs_temp | int(immediate, 2)
                    temp = hex(result)
                    registers[rt_dec] = '0x' + temp[2:].zfill(8)

                # andi
                elif opcode == '001100':
                    rs_temp = int(registers[rs_dec][2:], 16)
                    result = rs_temp & int(immediate, 2)
                    registers[rt_dec] = '0x' + hex(result)[2:].zfill(8)

                # slti
                elif opcode == '001010':
                    rs_temp = int(registers[rs_dec][2:], 16)
                    imm_temp = int(immediate, 2)
                    registers[rt_dec] = '0x00000001' if rs_temp < imm_temp else '0x00000000'


            # lw,  sw / rt, imm(rs)
            elif opcode[0:3] == '100' or opcode[0:3] == '101':
                inst_no += 1
                PC += 4

                # change to 2's complement if neg
                if int(immediate[0]) == 1:
                    list(immediate)
                    imm_comp = ''
                    for char in immediate:
                        if char == '1':
                            imm_comp += '0'
                        else:
                            imm_comp += '1'
                    imm = -(int(imm_comp, 2) + 1)
                else:
                    imm = int(immediate, 2)

                address_hex = hex(int(registers[rs_dec][2:], 16) + imm)
                address_idx = int(address_hex[2:], 16) - 0x10000000
                address_bin = bin(int(address_hex, 16))[2:].zfill(32)
                tag = address_bin[:cache_tag_size]
                set_idx = int(address_bin[cache_tag_size:cache_tag_size+cache_sets], 2)
                #print(f'address: ', address_hex)
                #print('tag: ', tag)
                #print('set_idx', set_idx)

                # lw
                if opcode == '100011':
                    c_tag = ""
                    if cache_type == '1':
                        if tag != c_tag.join(cache1[set_idx][:cache_tag_size]):
                            misses += 1
                            for i in range(cache_tag_size):
                                cache1[set_idx][i] = tag[i]
                        else:
                            hits += 1

                    elif cache_type == '2':
                        if tag != c_tag.join(cache2[set_idx][0][2:2+cache_tag_size]) and tag != c_tag.join(cache2[set_idx][1][2:2+cache_tag_size]):

                            misses += 1

                            if cache2[set_idx][0][0] == '0' and cache2[set_idx][1][0] == '0':
                                for i in range(cache_tag_size):
                                    cache2[set_idx][0][2+i] = tag[i]
                                for i in range(8):
                                    cache2[set_idx][0][35+i] = address_hex[2+i]
                                cache2[set_idx][0][0] = '1'  # valid = 1
                                cache2[set_idx][0][34] = '1'

                            elif cache2[set_idx][0][0] == '1' and cache2[set_idx][1][0] == '0':
                                for i in range(cache_tag_size):
                                    cache2[set_idx][1][2+i] = tag[i]
                                for i in range(8):
                                    cache2[set_idx][1][35+i] = address_hex[2+i]

                                cache2[set_idx][1][0] = '1'  # valid = 1
                                cache2[set_idx][0][34] = '0'

                            elif cache2[set_idx][0][0] == '0' and cache2[set_idx][1][0] == '1':
                                for i in range(cache_tag_size):
                                    cache2[set_idx][0][2+i] = tag[i]
                                for i in range(8):
                                    cache2[set_idx][0][35+i] = address_hex[2+i]

                                cache2[set_idx][0][0] = '1'  # valid = 1
                                cache2[set_idx][0][34] = '1'

                            else: # Both valid=1 (LRU)
                                if cache2[set_idx][0][34] == '0':

                                    # Check dirty bit & write back if needed
                                    if cache1[set_idx][0][1] == '1': # is Dirty
                                        cache1[set_idx][0][1] == '0'
                                        string = ""
                                        data_mem[address_idx] = string.join(cache1[set_idx][0][35:43])
                                        #print('update maemry: ', data_mem[address_idx])

                                    for i in range(cache_tag_size): # replace upper
                                        cache2[set_idx][0][2+i] = tag[i]
                                    for i in range(8):
                                        cache2[set_idx][0][35+i] = address_hex[2+i]

                                    cache2[set_idx][0][34] = '1'  # LRU

                                    # Check dirty bit & write back if needed
                                    if cache2[set_idx][0][1] == '1': # is Dirty
                                        cache2[set_idx][0][1] == '0'
                                        string = ""
                                        data_mem[address_idx] = string.join(cache2[set_idx][0][35:43])
                                        #print('Update memory(WB): ', data_mem[address_idx])


                                elif cache2[set_idx][0][34] == '1':

                                    # Check dirty bit & write back if needed
                                    if cache2[set_idx][1][1] == '1': # is Dirty
                                        cache2[set_idx][1][1] == '0'
                                        string = ""
                                        data_mem[address_idx] = string.join(cache2[set_idx][1][35:43])
                                        print('Update memory(WB): ', data_mem[address_idx])

                                    for i in range(cache_tag_size): # replace under
                                        cache2[set_idx][1][2+i] = tag[i]
                                    for i in range(8):
                                        cache2[set_idx][1][35+i] = address_hex[2+i]

                                    cache2[set_idx][0][34] = '0'  # LRU

                                    # Check dirty bit & write back if needed
                                    if cache2[set_idx][1][1] == '1': # is Dirty
                                        cache2[set_idx][1][1] == '0'
                                        string = ""
                                        data_mem[address_idx] = string.join(cache2[set_idx][1][35:43])
                                        #print('Update memory(WB): ', data_mem[address_idx])


                                else:
                                    print('error when both valid')


                        else:
                            hits += 1

                            if tag == c_tag.join(cache2[set_idx][0][2:2+cache_tag_size]):
                                cache2[set_idx][0][34] = '1'
                            elif tag == c_tag.join(cache2[set_idx][1][2:2+cache_tag_size]):
                                cache2[set_idx][0][34] = '0'
                            else:
                                print('error in cache2 hit')


                    registers[rt_dec] = '0x' + str(data_mem[address_idx])
                    #print(f'loaded: ', data_mem[address_idx])

                # sw
                elif opcode == '101011':
                    c_tag = ""

                    # NO write allocate(Cache unchanged)
                    if cache_type == '1':
                        if tag != c_tag.join(cache1[set_idx][:cache_tag_size]):
                            misses += 1

                        else:
                            hits += 1

                        data_mem[address_idx] = registers[rt_dec][2:]
                        #print(f'stored: ', data_mem[address_idx])

                    # Write-back(dirty bit), write allocate(fetch)
                    elif cache_type == '2':
                        if tag != c_tag.join(cache2[set_idx][0][:cache_tag_size]) and tag != c_tag.join(cache2[set_idx][1][:cache_tag_size]):
                            misses += 1

                            if cache2[set_idx][0][0] == '0' and cache2[set_idx][1][0] == '0':
                                for i in range(cache_tag_size):
                                    cache2[set_idx][0][2+i] = tag[i]
                                for i in range(8):
                                    cache2[set_idx][0][35+i] = address_hex[2+i]

                                cache2[set_idx][0][0] = '1'  # valid = 1
                                cache2[set_idx][0][34] = '1' # LRU
                                cache2[set_idx][0][1] = '1'  # Dirty = 1

                            elif cache2[set_idx][0][0] == '1' and cache2[set_idx][1][0] == '0':
                                for i in range(cache_tag_size):
                                    cache2[set_idx][1][2+i] = tag[i]
                                for i in range(8):
                                    cache2[set_idx][1][35+i] = address_hex[2+i]

                                cache2[set_idx][1][0] = '1'  # valid = 1
                                cache2[set_idx][0][34] = '0' # LRU
                                cache2[set_idx][1][1] = '1'  # Dirty = 1

                            elif cache2[set_idx][0][0] == '0' and cache2[set_idx][1][0] == '1':
                                for i in range(cache_tag_size):
                                    cache2[set_idx][0][2+i] = tag[i]
                                for i in range(8):
                                    cache2[set_idx][0][35+i] = address_hex[2+i]

                                cache2[set_idx][0][0] = '1'  # valid = 1
                                cache2[set_idx][0][34] = '1' #LRU
                                cache2[set_idx][0][1] = '1'  # Dirty = 1

                            else: # Both valid=1 (LRU)
                                if cache2[set_idx][0][34] == '0':
                                    if cache2[set_idx][0][1] == '1': # Check DIRTY bit
                                        cache2[set_idx][0][1] == '0' # DIRTY bit
                                        data_mem[address_idx] = registers[rt_dec][2:]
                                        #print(f'stored: ', data_mem[address_idx])

                                    for i in range(cache_tag_size):
                                        cache2[set_idx][0][2+i] = tag[i]
                                    for i in range(8):
                                        cache2[set_idx][0][35+i] = address_hex[2+i]

                                    if cache2[set_idx][0][1] == '1': # Check DIRTY bit
                                        cache2[set_idx][0][1] == '0' # DIRTY bit
                                        string = ""
                                        data_mem[address_idx] = string.join(cache2[set_idx][0][35:43])
                                        #print(f'Update memory(WB): ', data_mem[address_idx])

                                    cache2[set_idx][0][34] = '1'  # LRU
                                    cache2[set_idx][0][1] = '1'  # Dirty



                                else:
                                    if cache2[set_idx][1][1] == '1': # Check DIRTY bit
                                        cache2[set_idx][1][1] == '0' # DIRTY bit
                                        data_mem[address_idx] = registers[rt_dec][2:]
                                        #print(f'stored: ', data_mem[address_idx])

                                    for i in range(cache_tag_size):
                                        cache2[set_idx][1][2+i] = tag[i]
                                    for i in range(8):
                                        cache2[set_idx][1][35+i] = address_hex[2+i]

                                    if cache2[set_idx][0][1] == '1': # Check DIRTY bit
                                        #cache2[set_idx][0][1] == '0' # DIRTY bit
                                        string = ""
                                        data_mem[address_idx] = string.join(cache2[set_idx][0][35:43])
                                        #print(f'Update memory(WB): ', data_mem[address_idx])

                                    cache2[set_idx][0][34] = '0'  # LRU
                                    cache2[set_idx][1][1] = '1'  # Dirty

                            #data_mem[address_idx] = registers[rt_dec][2:]
                            #print(f'stored: ', data_mem[address_idx])

                        else:
                            #print('store hit!')
                            hits += 1

                            if tag == c_tag.join(cache2[set_idx][0][2:2+cache_tag_size]):
                                cache2[set_idx][0][34] = '1'
                            elif tag == c_tag.join(cache2[set_idx][1][2:2+cache_tag_size]):
                                cache2[set_idx][0][34] = '0'
                            else:
                                print('error in cache2 hit')

                            # NO update in MAIM memory for store hit



            # lui / re, imm
            elif opcode == '001111':
                temp = hex(int(immediate, 2))
                registers[int(rt, 2)] = '0x' + temp[2:].zfill(4) + '0000'
                PC += 4
                inst_no += 1

            # bne, beq / rs, rt, label
            elif opcode[0:4] == '0001':
                inst_no += 1

                if int(immediate[0]) == 1:
                    list(immediate)
                    imm_comp = ''
                    for char in immediate:
                        if char == '1':
                            imm_comp += '0'
                        else:
                            imm_comp += '1'
                    imm = -(int(imm_comp, 2)+1)
                else:
                    imm = int(immediate, 2)

                # bne
                if opcode == '000101':
                    if registers[rs_dec] != registers[rt_dec]:
                        PC += (4 + imm * 4)
                    else:
                        PC += 4
                        #print(f'current pc: {hex(PC)}')
                # beq
                if opcode == '000100':
                    if registers[rs_dec] == registers[rt_dec]:
                        PC += (4 + imm * 4)
                    else:
                        PC += 4


            # J-type instructions
            # j, jal / label
            elif opcode[0:4] == '0000':
                inst_no += 1
                if int(target[0]) == 1:
                    list(target)
                    tar_comp = ''
                    for char in target:
                        if char == '1':
                            tar_comp += '0'
                        else:
                            tar_comp += '1'
                    tar = -(int(tar_comp, 2)+1)
                else:
                    tar = int(target, 2)

                # jal
                if opcode == '000011':
                    tar_add = str(bin(int(inst_mem[PC//4][0], 16)))[2:6] + str(bin(tar*4))[2:].zfill(26)
                    registers[31] = '0x' + hex(PC + 4)[2:].zfill(8)
                    PC = int(tar_add, 2)
                    #print(f'address: {PC}')

                # j
                elif opcode == '000010':
                    tar_add = str(bin(int(inst_mem[PC//4][0], 16)))[2:6] + str(bin(tar*4))[2:].zfill(26)
                    PC = int(tar_add, 2)
                    #print(f'add: {tar_add}')


            else:
                print("error in I/J type")

            continue

        PC = hex(PC).upper() # int to str


    print(f'Instructions: {inst_no-1}')
    print(f'Total: {hits+misses}')
    print(f'Hits: {hits}\nMisses: {misses}')


if __name__ == '__main__':

    cache_type = sys.argv[1]
    block_size = sys.argv[2]
    inst_num = sys.argv[3]
    inst_file = sys.argv[4]

    if len(sys.argv) == 6:
        data_file = sys.argv[5]
    else:
        data_file = None
    machine_code_2_assembly(cache_type, block_size, inst_num, inst_file, data_file)
