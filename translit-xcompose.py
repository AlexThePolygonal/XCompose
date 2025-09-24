eng_dict = {}
ru_dict = {}
transliteration_dict = {}
import unicodedata


with open("parallel-symbols.txt", 'r') as f:
    text = f.read()

eng_lines, ru_lines = text.split(">==SEPARATOR==<\n")

for e, r in zip(eng_lines.splitlines(), ru_lines.splitlines()):
    transliteration_dict[e[3:]] = r[3:]

# print(transliteration_dict)


def line_is_trivial(line):
    return len(line) == 0 or line[0] != "<"

def change_compose_line(line, f):
    if line_is_trivial(line):
        return line, "", False
    key_parts = line.split("\"")
    assert len(key_parts) >= 3
    for i in range(len(key_parts)):
        if i != 1:
            key_parts[i] = ''.join(key_parts[i].split(" "))
    line = "\"".join(key_parts)
    code, payload = line.split(":")
    
    def get_next_code(c):
        idx = c.find(">")
        return c[1:idx], c[idx+1:]

    symbol_list = []

    while len(code) > 0:
        cur, code = get_next_code(code)
        symbol_list.append(cur)
    
    payload = payload[1:]
    payload = (payload[0:payload.find("\"")])
    code = ""
    descr = ""
    if (len(payload) == 1):
        code = (hex(ord(payload)))
        code = "U" + code[2:].upper()
        descr = (unicodedata.name(payload[0]))
    
    def merge_symbols(a):
        return "<" + "> <".join(a) + ">"
    
    is_unchanged = True
    for s in symbol_list:
        if s != f(s):
            is_unchanged = False
            break
    
    return merge_symbols(list(map(f, symbol_list))), " : \"" + payload + "\" " + code +" # " + descr, is_unchanged

        
text = "" 

with open("XCompose-draft", 'r') as f:
    text = f.read()

def remake_text(f, keep_unchanged=True):
    text_pairs = []
    for line in text.splitlines():
        a, b, is_unchanged = change_compose_line(line, f)
        if keep_unchanged or not is_unchanged:
            text_pairs.append((a,b))
    maxlen = 0
    for a, b in text_pairs:
        if b != "":
            if len(a) >= maxlen:
                maxlen = len(a)
    res_lines = []
    for (a,b) in text_pairs:
        if b != "":
            a = a + " "*(maxlen - len(a))
        res_lines.append(a + b)
    return "\n".join(res_lines)
    

def transform_to_rus(x):
    return transliteration_dict.get(x, x)

print("include \"%L\"")
print()
print(remake_text(lambda x:x))
print("""
########################################
#      RUSSIAN TRANSLIT VERSION        #
########################################
""")
print(remake_text(transform_to_rus, keep_unchanged=False))