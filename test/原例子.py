# encoding=utf8
import sys

reload(sys)
sys.setdefaultencoding('utf8')

from PyMacroParser import PyMacroParser

a1 = PyMacroParser()
a2 = PyMacroParser()
filename = u"../data/原问题中的例子.cpp"
print(filename)
a1.load(filename)
filename = u"../gen/b.cpp"
a1.dump(filename)  # 没有预定义宏的情况下，dump cpp
a2.load(filename)
a2.dumpDict()
a1.preDefine("MC1;MC2")  # 指定预定义宏，再dump
a1.dumpDict()
a1.dump(u"../gen/c.cpp")
