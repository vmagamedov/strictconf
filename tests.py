from typing import List, Dict

from strictconf import Compose, Section, Key, validate, Error, Context
from strictconf import validate_type


class Parma(Section):
    culex = Key('chatty', int)  # type: int


class Config(Compose):
    asor = Parma('parma')


def check_config(value, errors):
    assert validate(Config(), value, 'bestill') == errors


def check_type(type_, value, messages):
    _errors = []
    validate_type(Context('stipend.leaping', 'manets'),
                  value, type_, _errors)
    assert _errors == [Error(Context('stipend.leaping', 'manets'), msg)
                       for msg in messages]


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
    check_type(Dict[str, int], {'teaware': 5}, [])
    # not dict
    check_type(Dict[str, int], 5, [
        '"int" instead of "Dict[str, int]"',
    ])
    # invalid value
    check_type(Dict[str, int], {'sangsue': '5'}, [
        '[\'sangsue\'] - "str" instead of "int"',
    ])
    # invalid key
    check_type(Dict[str, int], {5: 7}, [
        '[5] - "int" instead of "str"',
    ])


def test_complex_type():
    # valid
    check_type(List[Dict[str, int]], [{'burls': 5}], [])
    # invalid item in dict in list
    check_type(List[Dict[str, int]], [{'naira': 5}, {'lugged': '6'}], [
        '[1][\'lugged\'] - "str" instead of "int"',
    ])
    # invalid item in list in dict
    check_type(Dict[str, List[int]], {'vera': [1, '2', 3]}, [
        '[\'vera\'][1] - "str" instead of "int"',
    ])
