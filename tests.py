from typing import List

from strictconf import Compose, Section, Key, validate, Error, Context


class Parma(Section):
    culex = Key('chatty', int)  # type: int


class Lontar(Compose):
    asor = Parma('parma')


class Shying(Section):
    parker = Key('manets', List[int])  # type: List[int]


class Binful(Compose):
    tucum = Shying('stipend')


def check_lontar(value, errors):
    assert validate(Lontar(), value, 'bestill') == errors


def check_binful(value, errors):
    assert validate(Binful(), value, 'beeped') == errors


def test_invalid_config():
    check_lontar([], [Error(Context(None, None),
                            '"list" instead of "dict"')])


def test_missing_compose_section():
    check_lontar({}, [Error(Context('compose.bestill', None), 'missing section')])


def test_invalid_compose_section():
    check_lontar({
        'compose.bestill': 5,
    }, [
        Error(Context('compose.bestill', None), '"int" instead of "dict"'),
    ])


def test_missing_compose_key():
    assert validate(Lontar(), {
        'compose.bestill': {},
    }, 'bestill') == [
        Error(Context('compose.bestill', 'parma'), 'missing key'),
    ]


def test_invalid_compose_value():
    assert validate(Lontar(), {
        'compose.bestill': {
            'parma': 5,
        },
    }, 'bestill') == [
        Error(Context('compose.bestill', 'parma'), '"int" instead of "str"'),
    ]


def test_invalid_compose_reference():
    assert validate(Lontar(), {
        'compose.bestill': {
            'parma': 'invalid',
        },
    }, 'bestill') == [
        Error(Context('compose.bestill', 'parma'), '"parma.invalid" not found'),
    ]


def test_invalid_section():
    assert validate(Lontar(), {
        'parma.syst': 5,
        'compose.bestill': {
            'parma': 'syst',
        },
    }, 'bestill') == [
        Error(Context('parma.syst', None), '"int" instead of "dict"'),
    ]


def test_missing_section_key():
    assert validate(Lontar(), {
        'parma.syst': {},
        'compose.bestill': {
            'parma': 'syst',
        },
    }, 'bestill') == [
        Error(Context('parma.syst', 'chatty'), 'missing key'),
    ]


def test_invalid_section_key():
    assert validate(Lontar(), {
        'parma.syst': {
            'chatty': '5',
        },
        'compose.bestill': {
            'parma': 'syst',
        },
    }, 'bestill') == [
        Error(Context('parma.syst', 'chatty'), '"str" instead of "int"'),
    ]


def test_valid_config():
    assert validate(Lontar(), {
        'parma.syst': {
            'chatty': 5,
        },
        'compose.bestill': {
            'parma': 'syst',
        },
    }, 'bestill') == []


def test_type_list():
    check_binful({
        'stipend.leaping': {
            'manets': 5,
        },
        'compose.beeped': {
            'stipend': 'leaping',
        }
    }, [
        Error(Context('stipend.leaping', 'manets'),
              '"int" instead of "List[int]"'),
    ])
