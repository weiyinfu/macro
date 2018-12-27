# encoding=utf8
import os
import sys

reload(sys)
sys.setdefaultencoding('utf8')


class pp:
    """
    自定义打印函数，相当于日志
    """

    @staticmethod
    def cout(*s):
        def findCaller():
            f = sys._getframe(1)
            if f is not None:
                f = f.f_back
            co = f.f_code
            return co.co_filename, f.f_lineno, co.co_name

        # 带行号的打印
        file, line, func = findCaller()
        file = os.path.relpath(file, os.curdir)
        if func != "<module>":
            info = "%s:%s(%s)" % (file, line, func)
        else:
            info = "%s:%s" % (file, line)
        print info, ' '.join(map(str, s))


escape_table = {
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
    '\\': "\\\\",
    '\a': '\\a',
    "\f": "\\f",
    "\v": '\\v',
    # "\?": "\\?",#C++中问号转不转义均可，python中无需转义
    '\'': '\\\'',  # C++和Python中单引号都是转不转义均可
    "\"": "\\\"",  # 双引号
    "\0": '\\\0',  # TODO:字符串处理截断
    # "\ddd"\xer" #字符映射转义使用逻辑来处理，三位八进制，两位16进制
}
unescape_table = {v[1]: i for i, v in escape_table.items()}


def is_space(c):
    return c in "\t\n \r\v\f"


def is_number(c):
    return c >= '0' and c <= '9'


def escape(s):
    # 转义字符串，例如把"\n\t"变成"\\n\\t"
    a = []
    for i in s:
        a.append(escape_table.get(i, i))
    return ''.join(a)


def unescape(s):
    # 反转义，把已转义的字符串去掉转义
    a = []
    i = 0
    while i < len(s):
        if s[i] == '\\':
            if i + 1 < len(s) and s[i + 1] in unescape_table:
                a.append(unescape_table.get(s[i + 1], ))
                i += 2
                continue
            # TODO:转义映射八进制和16进制
            pass
        a.append(s[i])
        i += 1
    return ''.join(a)


def wait_for(s, index, waiting):
    """
    在字符串s中从index开始一直往后走，直到找到waiting为止
    :param s:
    :param index: 起始下标
    :param waiting: 正在等待的字符串
    :return: 等待字符串出现的位置
    """
    pp.cout("wait for ", escape(waiting))
    i = index
    while i < len(s):
        i += 1
        if s.startswith(waiting, i):
            break
    pp.cout("wait for over", escape(waiting), "=" * 10)
    return i


def wait_quote(s, index, waiting):
    assert waiting in '\'\"' and len(waiting) == 1, "this function can only wait quotes"
    pp.cout("wait_quote", escape(waiting))
    i = index
    while i < len(s):
        if s[i] == waiting:
            break
        if s[i] == '\\':  # 碰见转义字符了毫无疑问要跳过去，因为下一字符必定不是我想要的
            i += 2
        else:
            i += 1
    pp.cout("wait_quote over", escape(waiting), s[i - 5:], '=' * 10)
    return i


def skip_space(s, i):
    while i < len(s) and is_space(s[i]):
        i += 1
    return i


def tos(v):
    """
    把一个值变成一个字符串
    """
    if v is None:
        return ""
    if type(v) == str:
        return '"%s"' % escape(v)
    if type(v) == unicode:
        return 'L"%s"' % (escape(v))
    if type(v) == bool:
        return "true" if v else "false"
    if type(v) in (int, float):
        return str(v)  # TODO:判断是否大于2*31-1，若是，表明是无符号正整数，否则有符号
    if type(v) == tuple:
        return '{%s}' % (",".join([tos(i) for i in v]))
    assert False, "cannot handle type %s" % (type(v))


def remove_comment(s):
    # 去掉注释：包括行内注释和块注释
    pp.cout("remove comment")
    i = 0
    a = []
    while i < len(s):
        if s[i] == '"':
            j = wait_quote(s, i + 1, '"')
            assert j < len(s) and s[j] == '"', "string is incomplete %s" % s[i:]
            a.append(s[i:j + 1])
            i = j + 1
        elif s.startswith("//", i):
            i = wait_for(s, i, '\n')
            if i < len(s) and s[i] == '\n':
                a.append('\n')
            i += 1
        elif s.startswith("/*", i):
            i = wait_for(s, i, "*/")
            assert s.startswith("*/", i), "cannot find end block */ for %s" % (s[i:])
            i += 2
        else:
            a.append(s[i])
            i += 1
    pp.cout(escape("".join(a)))
    pp.cout("=" * 10, 'remove comment over')
    return ''.join(a)


def parse_define(line):
    """
    解析#define x [y] 形式的命令
    :param line:
    :return: 返回identifier和value
    """
    pp.cout("parse define ", line)
    i = 0
    while i < len(line) and not is_space(line[i]):  # 去掉#define
        i += 1
    assert line[:i] == "#define", "error format for line %s" % line
    identifier_start = i
    while identifier_start < len(line) and is_space(line[identifier_start]): identifier_start += 1
    identifier_end = identifier_start
    while identifier_end < len(line) and not is_space(line[identifier_end]):  identifier_end += 1  # 寻找标识符
    identifier = line[identifier_start:identifier_end]
    if identifier_end >= len(line):
        pp.cout("parse define over", line, '=' * 3)
        return identifier, None
    value = line[identifier_end:].strip()  # 值
    pp.cout("parse define over", line, '=' * 3)
    return identifier, parse_value(value)


def parse_value(s):
    # 解析define中的值
    if not s.strip():
        return ""
    if not s.startswith("{"):
        next_index, token = parse_single_value(s, 0)
        assert next_index == len(s), "single token error %s %s" % (s, next_index)
        return token
    else:
        # 必为复杂结构
        assert s.startswith("{") and s.endswith("}"), "must be body %s" % (s)
        next_i, value = parse_multi_value(s, 0)
        assert next_i == len(s)
        return value


def multi_str(s, beg):
    pp.cout(s[beg:])
    a = []
    assert s[beg] == "\"", "multi str error %s" % (s[beg:])
    i = beg
    while i < len(s):
        assert s[i] == '"', "beg should be \" bug now %s" % (s[i:])
        j = wait_quote(s, i + 1, "\"")
        assert j < len(s) and s[j] == '"', "incomplete string %s" % s[beg:]
        a.append(s[i + 1:j])
        j = skip_space(s, j + 1)
        if j >= len(s):
            i = len(s)
            break
        i = j
        if s[i] == '"':
            continue
        else:
            break
    return min(i, len(s)), "".join(a)


def parse_single_value(s, beg):
    """
    解析单值类型
    :param s: 字符串
    :param beg:开始下标
    :return: 下标，单值
    """
    pp.cout("parse single value", escape(s[beg:]), "start index ", beg)
    if s[beg] == '"':
        next_i, big_str = multi_str(s, beg)
        return next_i, str(unescape(big_str))
    if s.startswith("L\"", beg):
        j = wait_quote(s, beg + 2, "\"")
        assert j < len(s) and s[j] == '"', "incomplete string %s" % s[beg:]
        return j + 1, unicode(unescape(s[beg + 2:j]))
    if s[beg] == "'":
        j = wait_quote(s, beg + 1, "'")
        assert j < len(s) and s[j] == "'", "incomplete char %s" % s[beg:]
        ch = unescape(s[beg + 1:j])
        assert len(ch) == 1, "parse char error (parsed=%s,s=%s)" % (ch, s)
        return j + 1, ord(ch)
    if s.startswith("true", beg):
        return beg + len("true"), True
    if s.startswith("false", beg):
        return beg + len("false"), False
    assert (s[beg] >= '0' and s[beg] <= '9') or s[beg] == '.', 'must be a number %s' % s
    next_index, v = parse_number(s, beg)
    return next_index, v


def get_number_pattern(s):
    """
    获取数字模式，如-234.34变成-23.23
    :param s:
    :return:
    """
    pp.cout("parse pattern", escape(s))
    a = []
    b = []
    i = 0
    while i < len(s):
        if s[i] >= '0' and s[i] <= '9':
            j = i
            while j < len(s) and s[j] >= '0' and s[j] <= '9':
                j += 1
            b.append(int(s[i:j]))
            a.append("d")
            i = j
        else:
            a.append(s[i])
            i += 1
    return ''.join(a), b


def parse_multi_value(s, beg):
    pp.cout("parse multi value", escape(s[beg:]), beg)
    tokens = []
    i = beg + 1  # 跳过{
    while i < len(s):
        if is_space(s[i]):
            i = skip_space(s, i)
            continue
        if s[i] == ',':
            i += 1
            continue
        if s[i] == '}':
            break
        if s[i] == '{':
            next_i, value = parse_multi_value(s, i)
            tokens.append(value)
            i = next_i
        else:
            next_i, value = parse_single_value(s, i)
            tokens.append(value)
            # 跳过若干个空白
            i = skip_space(s, next_i)
            # 单值后面，必然是逗号，或者结束
            assert s[i] == ',' or s[i] == '}', "error format %s" % s[i:]
    return i + 1, tuple(tokens)


def parse_number(s, beg):
    i = beg
    # 数字类型中间肯定没有空白，先把一个token找到再说
    while i < len(s) and not is_space(s[i]) and s[i] not in ',}': i += 1
    end = i
    s = s[beg:end]
    assert len(s.strip()), 'parse number error %s' % (s)
    if s.endswith("f") or s.endswith("F"):
        return end, float(s[:-1])
    if s.endswith("u") or s.endswith('U'):  # 考虑16进制表示负数，先确定类型再确定数值
        v = int(s[:-1])
        if v > 2 ** 32 - 1:  # 无符号整型不能太大
            raise Exception("number too large %s" % (s))
        return end, v
    if s.startswith("0") and not s.startswith("0x"):
        return end, int(s[1:], 8)
    if s.startswith("0x"):
        return end, int(s[2:], 16)
    # 用户没有声明格式，需要手动判定
    pattern, b = get_number_pattern(s)
    # 浮点数的100种表示方法
    # TODO：浮点数和正整数的常量表示法非常多
    if pattern in ("d.d", "-d.d",
                   "ded", "-ded", "de-d", "-de-d",
                   "d.", "-d.", ".d", "-.d"):
        return end, float(s)
    if pattern == "d" or pattern == "-d":
        # 默认是有符号整型
        # TODO:判断是否需要转换成负数
        return end, b[0]
    assert False, "error value single value s=%s pattern=%s" % (s, pattern)


def deep_copy(x):
    if x is None:
        return None
    if type(x) != tuple:
        assert type(x) in (int, float, unicode, str, bool), "unrecognized type %s" % (type(x))
        return x
    a = []
    for i in x:
        a.append(deep_copy(i))
    return tuple(a)


def parse(lines, define):
    """
    :param lines: 每行指令
    :param define: 现有的一些变量
    :return:
    """
    pp.cout("define", define)
    i = 0
    q = [True]
    while i < len(lines):
        pp.cout(lines[i], q)
        if lines[i].startswith("#ifdef"):
            identifier = lines[i].split()[1]
            q.append(define.exist(identifier))
        elif lines[i].startswith("#ifndef"):
            identifier = lines[i].split()[1]
            q.append(not define.exist(identifier))
        elif lines[i].startswith("#endif"):
            q.pop()
        elif lines[i].startswith("#else"):
            q[-1] = not q[-1]
        elif lines[i].startswith("#undef"):
            identifier = lines[i].split()[1]
            if define.exist(identifier):
                define.remove(identifier)
        elif lines[i].startswith("#define"):
            if all(q):  # 只有队列中全部为真才可以执行
                identifier, value = parse_define(lines[i])
                define.put(identifier, value)
        else:
            if q[-1]:
                assert False, "cannot parse " + lines[i]
        i += 1


class OrderedDict:
    """
    自定义有序字典，使得最终define的顺序就是正确的顺序，本质上相当于一个LRU
    """

    def __init__(self):
        self.dic = dict()
        self.ks = list()

    def put(self, k, v):
        self.remove(k)
        self.ks.append(k)
        self.dic[k] = v

    def items(self):
        return list((i, self.dic[i]) for i in self.ks)

    def keys(self):
        return self.ks

    def values(self):
        return [self.dic[i] for i in self.ks]

    def remove(self, k):
        if k not in self.dic:
            return
        else:
            del self.ks[self.ks.index(k)]
            del self.dic[k]

    def exist(self, k):
        return k in self.dic

    def get(self, k):
        return self.dic.get(k)

    def clear(self):
        self.__init__()

    def update(self, kv):
        for k, v in kv.items():
            self.put(k, v)


class PyMacroParser:
    def __init__(self):
        self.defines = OrderedDict()
        self.lines = []

    def load(self, f):
        self.lines = [i.strip() for i in remove_comment(open(f).read()).split('\n') if i.strip()]
        parse(self.lines, self.defines)

    def preDefine(self, s):
        self.defines.clear()
        self.defines.update({k.strip(): None for k in s.strip().split(';') if k.strip()})
        parse(self.lines, self.defines)

    def dump(self, f):
        file = open(f, 'w')
        for k, v in self.defines.items():
            file.write("#define %s %s\n" % (k, tos(v)))

    def dumpDict(self):
        return {i: deep_copy(v) for i, v in self.defines.items()}


if __name__ == '__main__':
    parser = PyMacroParser()
    filename = u"字符串拼接.cpp"
    # filename = u"测试流程2.cpp"
    parser.preDefine("MC1;MC2")
    parser.load("data/" + filename)
    parser.dump("gen/" + filename)
    print(parser.dumpDict())
