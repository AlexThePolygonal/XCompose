import unicodedata

def print_list(idxs):
    for idx in idxs:
        res = ""
        res += "<Multi_key> <r> : "
        res += "\"" + chr(idx) + "\""
        res += " U" + format(idx, 'X') + " # "
        res += unicodedata.name(chr(idx))
        print(res)

print_list(range(0x2160, 0x216C))
print_list(range(0x2170, 0x217C))
