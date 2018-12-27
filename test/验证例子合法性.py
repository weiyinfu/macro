# encoding=utf8
import sys

reload(sys)
sys.setdefaultencoding('utf8')

"""
运行编译命令，保证全部测试用例都能够通过编译
"""
import os

if not os.path.exists("../temp"):
    os.mkdir("../temp")
main_func = """
int main(){return 0;}
"""
import platform

encoding = 'gbk' if platform.system().lower() == "windows" else "utf8"
for i in os.listdir("../data"):
    i = unicode(i.decode(encoding))
    filename = u"../data/" + i
    content = open(filename).read() + main_func
    open("../temp/" + i, 'w').write(content)
    cmd = u"g++ ../temp/" + i
    print(cmd)
    os.system(cmd.decode('utf8').encode(encoding))  # 内部处理用utf8，调用系统命令必须转换回去
os.remove("a.exe")
