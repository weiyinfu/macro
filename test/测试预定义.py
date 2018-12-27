import PyMacroParser as p

parser = p.PyMacroParser()
parser.preDefine("ha;ba;hei")
print(parser.dumpDict())
