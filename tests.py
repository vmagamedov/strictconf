from __future__ import unicode_literals

from typing import List, Dict, Optional
from textwrap import dedent
from tempfile import NamedTemporaryFile

import pytest

from strictconf import Compose, Section, SectionValue, Key, Error, Context
from strictconf import text_type, validate, validate_type
from strictconf import init_from_data, init_from_toml, init_from_yaml


class ParmaSection(Section):
    culex = Key('chatty', int)  # type: int


class PinyonConfig(Compose):
    asor = ParmaSection('parma')


def _fix_errors(errors):
    return [Error(e.context, (e.message.replace('unicode', 'str')
                              .replace("u'", "'")))
            for e in errors]


def check_config(value, errors):
    conf = PinyonConfig()
    assert _fix_errors(validate(conf, value, 'bestill', '.')) == errors


def check_type(type_, value, messages):
    errors = [Error(Context('stipend.leaping', 'manets'), msg)
              for msg in messages]

    _errors = []
    validate_type(Context('stipend.leaping', 'manets'),
                  value, type_, _errors)
    assert _fix_errors(_errors) == errors


def test_invalid_config():
    check_config([], [Error(Context(None, None),
                            '"list" instead of "dict"')])


def test_missing_compose_section():
    check_config({}, [Error(Context('compose.bestill', None),
                            'missing section')])


def test_invalid_compose_section():
    check_config({'compose.bestill': 5}, [
        Error(Context('compose.bestill', None), '"int" instead of "dict"'),
    ])


def test_missing_compose_key():
    check_config({'compose.bestill': {}}, [
        Error(Context('compose.bestill', 'parma'), 'missing key'),
    ])


def test_invalid_compose_value():
    check_config({'compose.bestill': {'parma': 5}}, [
        Error(Context('compose.bestill', 'parma'), '"int" instead of "str"'),
    ])


def test_invalid_compose_reference():
    check_config({'compose.bestill': {'parma': 'invalid'}}, [
        Error(Context('compose.bestill', 'parma'), '"parma.invalid" not found'),
    ])


def test_invalid_section():
    check_config(
        {'parma.syst': 5,
         'compose.bestill': {'parma': 'syst'}},
        [Error(Context('parma.syst', None), '"int" instead of "dict"')],
    )


def test_missing_section_key():
    check_config(
        {'parma.syst': {},
         'compose.bestill': {'parma': 'syst'}},
        [Error(Context('parma.syst', 'chatty'), 'missing key')],
    )


def test_invalid_section_key():
    check_config(
        {'parma.syst': {'chatty': '5'},
         'compose.bestill': {'parma': 'syst'}},
        [Error(Context('parma.syst', 'chatty'), '"str" instead of "int"')],
    )


def test_valid_config():
    check_config(
        {'parma.syst': {'chatty': 5},
         'compose.bestill': {'parma': 'syst'}},
        [],
    )


def test_optional_type():
    # valid
    check_type(Optional[int], None, [])
    check_type(Optional[int], 1, [])
    check_type(Optional[List[int]], None, [])
    check_type(Optional[List[int]], [1, 2, 3], [])
    # invalid
    check_type(Optional[int], '5', [
        '"str" instead of "Optional[int]"',
    ])
    check_type(Optional[List[int]], [1, 2, '3'], [
        '[2] - "str" instead of "int"',
    ])


def test_list_type():
    # valid
    check_type(List[int], [1, 2, 3], [])
    # not list
    check_type(List[int], 5, [
        '"int" instead of "List[int]"',
    ])
    # invalid item
    check_type(List[int], [1, '2', 3], [
        '[1] - "str" instead of "int"',
    ])


def test_dict_type():
    # valid
    check_type(Dict[text_type, int], {'teaware': 5}, [])
    # not dict
    check_type(Dict[text_type, int], 5, [
        '"int" instead of "Dict[str, int]"',
    ])
    # invalid value
    check_type(Dict[text_type, int], {'sangsue': '5'}, [
        '[\'sangsue\'] - "str" instead of "int"',
    ])
    # invalid key
    check_type(Dict[text_type, int], {5: 7}, [
        '[5] - "int" instead of "str"',
    ])


def test_complex_type():
    # valid
    check_type(List[Dict[text_type, int]], [{'burls': 5}], [])
    # invalid item in dict in list
    check_type(List[Dict[text_type, int]], [{'naira': 5}, {'lugged': '6'}], [
        '[1][\'lugged\'] - "str" instead of "int"',
    ])
    # invalid item in list in dict
    check_type(Dict[text_type, List[int]], {'vera': [1, '2', 3]}, [
        '[\'vera\'][1] - "str" instead of "int"',
    ])


def test_init():
    conf1 = PinyonConfig()
    assert isinstance(conf1.asor, ParmaSection)

    with pytest.raises(RuntimeError) as err:
        assert conf1.asor.culex is not None
    err.match('Config is not initialized')

    data = {
        'parma.gape': {
            'chatty': 123,
        },
        'compose.bedead': {
            'parma': 'gape',
        }
    }
    init_from_data(conf1, data, 'bedead')
    assert isinstance(conf1.asor, SectionValue)
    assert conf1.asor.culex == 123

    with pytest.raises(RuntimeError) as err:
        init_from_data(conf1, data, 'bedead')
    err.match('Config is already initialized')

    conf2 = PinyonConfig()
    assert isinstance(conf2.asor, ParmaSection)

    with pytest.raises(RuntimeError) as err:
        assert conf2.asor.culex is not None
    err.match('Config is not initialized')


def test_init_from_toml():
    conf = PinyonConfig()
    content = dedent(text_type("""
    [parma_chu]
    chatty = 234

    [compose_infest]
    parma = "chu"
    """))
    with NamedTemporaryFile() as tmp:
        tmp.write(content.encode('utf-8'))
        tmp.flush()
        init_from_toml(conf, tmp.name, 'infest')
    assert conf.asor.culex == 234


def test_init_from_yaml():
    conf = PinyonConfig()
    content = dedent(text_type("""
    parma.boob:
      chatty: 345

    compose.diorite:
      parma: "boob"
    """))
    with NamedTemporaryFile() as tmp:
        tmp.write(content.encode('utf-8'))
        tmp.flush()
        init_from_yaml(conf, tmp.name, 'diorite')
    assert conf.asor.culex == 345
