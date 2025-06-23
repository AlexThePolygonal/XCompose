import unicodedata
from unidecode import unidecode

BEG = int(0x1D400)
END = int(0x1D7FF)

tag_mapping = {
    "DOUBLE-STRUCK" : "<b>",
    "FRAKTUR" : "<f>",
    "SANS-SERIF" : "<s>",
    "MONOSPACE" : "<m>",
    "ITALIC" : "<i>",
    "SCRIPT" : "<c>",
    "BOLD" : "<a>",
}

def find_tags(descr):
    res = []
    for k, v in tag_mapping.items():
        if k in descr:
            res.append(v)
    return res


def create_xcompose_line(idx):
    symb = chr(idx)
    descr = unicodedata.name(symb)
    tags = find_tags(descr.split())
    if len(tags) == 0:
        return ""
    if unidecode(symb) != '':
        command = "".join(list(map(lambda x : " <"+ x +"> ", [*unidecode(symb)])))
        return "<Multi_key> " + " ".join(tags) + " " + command + " : \"" +symb + "\" # " + descr + " " + hex(idx)
    return ""

for i in range(BEG, END):
    try:
        print(create_xcompose_line(i))
    except:
        pass