#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: whiledoing
# @Date:   2014-01-11 11:35:28
# @Last Modified by:   whiledoing
# @Last Modified time: 2014-01-13 15:41:10

''' test JsonParser '''

import os
import sys

from JsonParser import JsonParser
from copy import deepcopy

def assert_eq(a, b):
    if not a == b:
        print('assertion has failed:\n    expct: %r\n    given: %r' % (a, b))
        assert False


def check(s, d):
    ''' check basic operation of JsonParser'''

    # load and dump
    jp = JsonParser()
    jp.load(s)
    assert_eq(jp.dumpDict(), d)
    assert_eq(jp.dump(), s)

    # load and dump by another JsonParser
    jp2 = JsonParser()
    jp2.load(jp.dump())
    assert_eq(jp2.dumpDict(), jp.dumpDict())
    assert_eq(jp2.dump(), jp.dump())

    # check update
    jp3 = JsonParser()
    jp3.update(jp.dumpDict())
    assert_eq(jp3.dumpDict(), jp.dumpDict())
    assert_eq(jp3.dump(), jp.dump())

    # check file operation
    f = 'temp_for_test'
    jp.dumpJson(f)
    jp4 = JsonParser()
    jp4.loadJson(f)
    os.remove(f)
    assert_eq(jp4.dumpDict(), jp.dumpDict())
    assert_eq(jp4.dump(), jp.dump())


def check_invalid(s):
    jp = JsonParser()

    try:
        jp.load(s)
    except (TypeError, ValueError):
        assert True
    else:
        print('assertion has failed:\n    should raise an error when parsing %r\n' % s)
        assert False


def test_json_parser():
    # test back slash
    check('''{"a\\t\\b\\f\\r":"\\"help\\n"}''', {'a\t\b\f\r' : '"help\n'})

    # test empty dict and list
    check('''{"":[]}''', {'' : []})

    # test nested value && true, false, null
    check('''{"a":[1, true, {"a":""}, false, [{}], null], "b":"a"}''', {'a':[1, True, {'a':''}, False, [{}], None], 'b' : 'a'})

    # test number and float number
    check('''{"int":[1, 2, 3, 4, 10032, 3322323], "float":[3.12434, 2223.0, -0.0, 2.3e+20, -1.2e-10]}''',
        {'int':[1, 2, 3, 4, 10032, 3322323], 'float':[3.12434, 2223.0, -0.0, 2.3e+20, -1.2e-10]})

    # check error condition

    # begin with dict
    check_invalid('''[]''')
    # key value must be str
    check_invalid('''{1:2}''')
    # ':' seperator missing
    check_invalid('''{"1"3}''')
    # ',' seperator missing
    check_invalid('''{"1":2 "3":4}''')
    # '"' missing
    check_invalid('''{"1":"})''')
    # ']' missing
    check_invalid('''{"1":[1,2 }''')
    # '}' missing
    check_invalid('''{"1":{1,2 }''')
    # must using " as string type
    check_invalid("{''}")
    # invalid '\uxxxx'
    check_invalid('''{"\u"}''')
    check_invalid('''{"\ua"}''')
    check_invalid('''{"\uab"}''')
    check_invalid('''{"\uabc"}''')
    check_invalid('''{"\uabcg"}''')


def test_back_slash_forward_slash():
    # test '\/', support load '\/', but only write back '/'(according to simplejson)
    jp = JsonParser()
    jp.load('{"\\/":""}')
    assert_eq(jp.dump(), '{"/":""}')
    assert_eq(jp.dumpDict(), {'/':''})


def test_back_slash_u():
    # test \uxxxx
    s = ('''{"\\u00A9":""}''', {'\xa9':''})


def test_dict_related_operation():
    # test dict related operation, include 1) load only str key item 2) deepcopy original dict
    d_a = {'a': [1], 2:'notexist', 'nested':[{'a':'b', 3:2}, 2]}
    d_a_back = deepcopy(d_a)

    jp = JsonParser()
    jp.loadDict(d_a)

    # only copy str key item
    d_a_g = {'a':[1], 'nested':[{'a':'b'}, 2]}
    assert_eq(jp.dumpDict(), d_a_g)

    # dump get a deepcopy of jp dict
    d_d = jp.dumpDict()
    d_d['x'] = 'x'
    assert_eq(jp.dumpDict(), d_a_g)

    # not change origin dict && support [] operator
    jp['a'].append(2)
    jp['nested'][0]['c'] = 100
    assert_eq(jp['a'], [1, 2])
    assert_eq(d_a_back, d_a)


def run_test():
    ''' run all test method begin with prefix test'''
    for k,v in globals().items():
        if k.startswith('test'):
            v()


if __name__ == '__main__':
    run_test()
    print('all tests passed!')

