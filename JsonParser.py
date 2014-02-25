#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: whiledoing
# @Date:   2014-01-06 16:44:16
# @Last Modified by:   whiledoing
# @Last Modified time: 2014-01-13 15:34:30

from copy import deepcopy

class JsonParser:
    ''' Parse json file or string into a dict

        Parse json file or string into a dict, and still supports dump the
        dict back into json file
    '''
    def __init__(self):
        # saving json dict data
        self.data = dict()

        # back slash convert table
        self.parse_back_slash = {'\\"':'"', '\\/':'/', '\\\\':'\\', '\\b':'\b', '\\f':'\f', '\\n':'\n', '\\r':'\r', '\\t':'\t'}
        self.dump_back_slash = {}
        for k,v in self.parse_back_slash.items():
            self.dump_back_slash[v] = k
        # one exception, not translate slash(according to simplejson default processing logic)
        self.dump_back_slash.pop('/')

        # json key words
        self.keywords = ['{', '}', ':', ',', '[', ']']
        self.numbers = '.0123456789'
        self.bracket_pair = {'{': '}', '[': ']'}

        # parser when meets the bracket
        self.bracket_parser = {'{': self.__tokens2dict, '[': self.__tokens2list}

        # whether dump add space between sequences
        self.space_between_seq = True

        # default encoding
        self.default_encoding = 'utf-8'


    def setFileEncoding(encoding):
        '''设置默认文本编码

        在调用loadJson和调用dumpJson之前调用该方法，将会使用指定的编码对文本进行翻译
        '''
        self.default_encoding = encoding


    def load(self, s):
        '''读取json数据，输入s为一个json字符串，如果读取错误抛出异常'''
        if not isinstance(s, (str, unicode)):
            raise TypeError('s need to be a string or unicode type')

        if isinstance(s, str):
            s = unicode(s, self.default_encoding)

        self.data = self.__parse_json_tokens(self.__tokenize(s))


    def dump(self):
        '''根据类中数据返回字符串'''
        return self.__dump_one_object(self.data)


    def loadJson(self, f):
        '''从文件中读取json文件，f为路径名称，读取错误抛出异常'''
        with open(f, 'r') as json_file:
            return self.load(''.join(line.strip() for line in json_file))


    def dumpJson(self, f):
        '''将类中内容写入到json格式文件中，文件若存在则覆盖，文件操作失败抛出异常'''
        with open(f, 'w') as json_file:
            json_file.write(self.dump().encode(self.default_encoding))


    def loadDict(self, d):
        '''读取dict中的数据，存入到类中，若遇到不是字符串的key则忽略'''
        self.data = self.__filter_str_key_deepcopy_dict(d)


    def dumpDict(self):
        '''返回一个字典，包含类中数据'''
        return deepcopy(self.data)


    def update(self, d):
        '''使用字典d中数据更新当前类中字典'''
        self.data.update(self.__filter_str_key_deepcopy_dict(d))


    def __getitem__(self, item):
        if item not in self.data:
            raise KeyError('not exist key %s' % item)
        return self.data[item]


    def __setitem__(self, key, value):
        if not isinstance(key, unicode):
            raise TypeError("input key must be unicode type")
        self.data[key] = value


    def __str__(self):
        return str(self.data)


    def __repr__(self):
        return repr(self.data)


    def __filter_str_key_deepcopy_object(self, o):
        ''' deepcopy object o, keep only string type keys when meets dict object '''
        if isinstance(o, str):
            o = unicode(o)
        elif isinstance(o, list):
            o = self.__filter_str_key_deepcopy_list(o)
        elif isinstance(o, dict):
            o = self.__filter_str_key_deepcopy_dict(o)
        else:
            o = deepcopy(o)

        return o


    def __filter_str_key_deepcopy_list(self, l):
        ''' deepcopy list '''
        res = []
        for v in l:
            res.append(self.__filter_str_key_deepcopy_object(v))
        return res


    def __filter_str_key_deepcopy_dict(self, d):
        '''recursivly deepcopy dict d, filtering out none str or unicode type key items'''
        res = {}
        for k,v in d.items():
            if not isinstance(k, (str, unicode)): continue
            res[unicode(k)] = self.__filter_str_key_deepcopy_object(v)
        return res


    def __tokenize(self, s):
        '''Tokenize origin string into json tokens'''
        i = 0
        end = len(s)
        res = []

        while i < end:
            if s[i] in self.keywords: # keywords
                res.append(s[i])
                i += 1
            elif s[i] in self.numbers or s[i] == '-': # numbers or begin with negative charc
                b_i = i
                i += 1
                while i < end and s[i] in self.numbers:
                    i += 1

                if i < end and s[i] in ('eE'):
                    i += 1
                    if i < end and s[i] in ('+-'):
                        i += 1
                    while i < end and s[i] in self.numbers:
                        i += 1

                num = s[b_i:i]
                res.append(float(num) if num.count('.') > 0 else int(num))
            elif s[i] == '"': # str
                i += 1

                t_s = u''
                while i < end:
                    # meet back slash, convert into original data
                    if s[i] == '\\':
                        i += 1
                        if i == end:
                            raise ValueError('can not find end "')

                        back_slash_c = '\\' + s[i]

                        # execption '\uxxxx'
                        if back_slash_c == '\\u':
                            msg = 'invalid \\uXXXX escape sequence'
                            hex_num = s[i+1:i+5]
                            if len(hex_num) != 4:
                                raise ValueError(msg)

                            try: # convert to unicode
                                uni = int(s[i+1:i+5], 16)
                                t_s += unichr(uni)
                                i += 5
                            except ValueError:
                                raise ValueError(msg)

                            continue

                        if back_slash_c not in self.parse_back_slash:
                            raise ValueError('invalid \\%s escape' % s[i])
                        t_s += self.parse_back_slash[back_slash_c]
                    elif s[i] == '"':
                        break;
                    else:
                        t_s += s[i]

                    i += 1
                else:
                    raise ValueError('can not find end "')

                res.append(t_s)
                i += 1
            elif s[i] == 't' and i+4 < end and s[i:i+4] == 'true':
                res.append(True)
                i += 4
            elif s[i] == 'n' and i+4 < end and s[i:i+4] == 'null':
                res.append(None)
                i += 4
            elif s[i] == 'f' and i+5 < end and s[i:i+5] == 'false':
                res.append(False)
                i += 5
            elif s[i] in (' \t\n'): # bug fix : \t\n is also filtered
                i += 1
            else:
                raise ValueError('invalid json data at index %s' % i)

        return res


    def __parse_json_tokens(self, tokens):
        '''Parse json tokens return json dict'''
        if len(tokens) < 2 or tokens[0] != '{' or tokens[len(tokens)-1] != '}':
            raise ValueError('invalid json data : json data must begin as a dict')

        return self.__tokens2dict(tokens[1:-1])


    def __find_end(self, tokens, start_index):
        '''Find the end index of the matched close bracket

        Tokens[start_index] as the open bracket, and start searching end bracket
        from start_index, return the matched index of the close bracket
        '''
        assert(tokens[start_index] in self.bracket_pair)

        beg_c = tokens[start_index]
        end_c = self.bracket_pair[beg_c]

        c = 0
        for i in xrange(start_index + 1,len(tokens)):
            if tokens[i] == beg_c:
                c += 1
            elif tokens[i] == end_c:
                c -= 1
                if c == -1:
                    break
        else:
            raise ValueError('invalid json data : can\'t find end bracket  %s' % end_c)

        return i


    def __parse_one_object(self, tokens, index):
        '''Parse one object from tokens[index]

        Args:
            tokens: tokens for parse
            index: begin index

        Returns:
            return a tuple (curent object, next parse index)
        '''
        v = None

        # recursively parse
        if tokens[index] in self.bracket_pair:
            # find end index of the matching end bracket
            end_index = self.__find_end(tokens, index)

            # get the parser
            parser = self.bracket_parser[tokens[index]]

            # parser one object
            v = parser(tokens[index+1:end_index])
            index = end_index + 1
        else:
            v = tokens[index]
            index += 1

        return (index, v)


    def __tokens2dict(self, tokens):
        '''convert tokens into a dict'''
        res = {}
        end = len(tokens)
        index = 0

        while index < end:
            if not isinstance(tokens[index], unicode):
                raise ValueError('invalid json data : key value must be str type')

            # get key value
            k = tokens[index]
            index += 1

            # check ':'
            if index >= end or tokens[index] != ':':
                raise ValueError('invalid json data : can\'t find ":" in dict')
            index += 1

            # get one object
            (index, v) = self.__parse_one_object(tokens, index)

            # add one item into result
            res[k] = v

            # if not find the needed seperator ','
            if index < end and tokens[index] != ',':
                raise ValueError('invalid json data : can\'t find "," seperator')
            index += 1

        return res


    def __tokens2list(self, tokens):
        '''convert tokens into dict'''
        res = []
        end = len(tokens)
        index = 0

        while index < end:
            (index, v) = self.__parse_one_object(tokens, index)
            res.append(v)

            if index < end and tokens[index] != ',':
                raise ValueError('invalid json data : can\'t find "," seperator')
            index += 1

        return res


    def __dump_one_object(self, d):
        '''dump one object from d, convert into string format of json'''
        if isinstance(d, list):
            return self.__dump_list(d)
        elif isinstance(d, dict):
            return self.__dump_dict(d)
        elif isinstance(d, unicode):
            return self.__dump_str(d)
        elif d is True:
            return 'true'
        elif d is False:
            return 'false'
        elif d is None:
            return 'null'
        else:
            return unicode(d)


    def __dump_list(self, l):
        '''dump list l into string format of json'''
        assert(isinstance(l, list))
        sep = u', ' if self.space_between_seq else u','
        return '[%s]' % (sep.join((self.__dump_one_object(o) for o in l)))


    def __dump_dict(self, d):
        '''dump dict d into string format of json'''
        assert(isinstance(d, dict))
        sep = u', ' if self.space_between_seq else u','
        return '{%s}' % (sep.join((self.__dump_str(k) + u':' + self.__dump_one_object(v) for k,v in d.items())))


    def __dump_str(self, s):
        '''dump unicode s into string format of json'''
        assert(isinstance(s, unicode))
        res = u''.join((self.dump_back_slash[c] if c in self.dump_back_slash else c for c in s))
        return '"%s"' % res


if __name__ == '__main__':
    import test
    test.run_test()
