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
        return line, ""
    line = ''.join(line.split(" "))
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
    
    return merge_symbols(list(map(f, symbol_list))), " : \"" + payload + "\"  # " + descr

        


text = ""

with open("XCompose_original", 'r') as f:
    text = f.read()

def remake_text(f):
    text_pairs = []
    for line in text.splitlines():
        a, b = change_compose_line(line, f)
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
    
# print(remake_text(lambda x:x))

def transform_to_rus(x):
    return transliteration_dict.get(x, x)

print(remake_text(transform_to_rus))