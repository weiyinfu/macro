# encoding=utf8
import sys
import platform

reload(sys)
sys.setdefaultencoding('utf8')

import os
from PyMacroParser import PyMacroParser

files = os.listdir("../data")
encoding = "gbk" if platform.system().lower() == "windows" else "utf8"
for i in files:
    i = unicode(i.decode(encoding))
    filename = unicode(u"../data/" + i)
    p = PyMacroParser()
    p.load(filename)
    p.dump("../gen/" + i)
    print p.dumpDict()
    raw_input()
