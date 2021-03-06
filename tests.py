from __future__ import unicode_literals

from typing import List, Dict, Optional
from textwrap import dedent
from tempfile import NamedTemporaryFile

import pytest

import strictconf.data
import strictconf.toml
import strictconf.yaml

from strictconf import Compose, Section, Key, key_property
from strictconf.config import SectionValue
from strictconf.compat import is_type, type_name
from strictconf.checker import Error, validate, Context, validate_type


class ParmaSection(Section):
    culex = Key('chatty', int)  # type: int

    swatter = 42

    @key_property
    def scear(self):
        return self.culex + 1

    def ostraka(self):
        return self.culex + 2


class PinyonConfig(Compose):
    asor = ParmaSection('parma')

    @key_property
    def yalu(self):
        return self.asor.culex + 3

    @key_property
    def kennels(self):
        return self.asor.scear + 4

    def shylock(self):
        return self.asor.ostraka() + 5


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
        '"str" instead of "int"',
    ])
    check_type(Optional[List[int]], [1, 2, '3'], [
        '[2] - "str" instead of "int"',
    ])


def test_list_type():
    # valid
    check_type(List[int], [1, 2, 3], [])
    # not list
    check_type(List[int], 5, [
        '"int" instead of "typing.List[int]"',
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
        '"int" instead of "typing.Dict[str, int]"',
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


def test_data_init():
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
    strictconf.data.init(conf1, data, 'bedead')
    assert isinstance(conf1.asor, SectionValue)
    assert conf1.asor.culex == 123

    with pytest.raises(RuntimeError) as err:
        strictconf.data.init(conf1, data, 'bedead')
    err.match('Config is already initialized')

    conf2 = PinyonConfig()
    assert isinstance(conf2.asor, ParmaSection)

    with pytest.raises(RuntimeError) as err:
        assert conf2.asor.culex is not None
    err.match('Config is not initialized')


def test_toml_init():
    conf = PinyonConfig()
    content = dedent("""
    [parma_chu]
    chatty = 234

    [compose_infest]
    parma = "chu"
    """)
    with NamedTemporaryFile() as tmp:
        tmp.write(content.encode('utf-8'))
        tmp.flush()
        strictconf.toml.init(conf, [tmp.name], 'infest')
    assert conf.asor.culex == 234


def test_yaml_init():
    conf = PinyonConfig()
    content = dedent("""
    parma.boob:
      chatty: 345

    compose.diorite:
      parma: "boob"
    """)
    with NamedTemporaryFile() as tmp:
        tmp.write(content.encode('utf-8'))
        tmp.flush()
        strictconf.yaml.init(conf, [tmp.name], 'diorite')
    assert conf.asor.culex == 345


def test_key_property():
    conf = PinyonConfig()
    data = {
        'parma.gape': {
            'chatty': 123,
        },
        'compose.bedead': {
            'parma': 'gape',
        }
    }
    strictconf.data.init(conf, data, 'bedead')

    assert conf.asor.swatter == 42
    assert conf.asor.scear == conf.asor.culex + 1
    assert conf.asor.ostraka() == conf.asor.culex + 2
    assert conf.yalu == conf.asor.culex + 3
    assert conf.kennels == conf.asor.scear + 4
    assert conf.shylock() == conf.asor.ostraka() + 5


def test_keyless():
    class Anomy(Section):
        jog: int

        judgeth: int = 42  # non-configurable

        @key_property
        def tumour(self):
            return self.jog + 1

        def alkyne(self):
            return self.jog + 2

    class HokkuConfig(Compose):
        crote: Anomy

        @key_property
        def hipe(self):
            return self.crote.jog + 3

        @key_property
        def hopple(self):
            return self.crote.tumour + 4

        def snip(self):
            return self.crote.alkyne() + 5

    assert Anomy.judgeth == 42
    assert set(Anomy.__keys__.keys()) == {'jog'}

    conf = HokkuConfig()
    data = {
        'crote.fasting': {
            'jog': 123,
        },
        'compose.exodus': {
            'crote': 'fasting',
        },
    }
    strictconf.data.init(conf, data, 'exodus')

    assert conf.crote.jog == data['crote.fasting']['jog']
    assert conf.crote.judgeth == 42
    assert conf.crote.tumour == conf.crote.jog + 1
    assert conf.crote.alkyne() == conf.crote.jog + 2
    assert conf.hipe == conf.crote.jog + 3
    assert conf.hopple == conf.crote.tumour + 4
    assert conf.snip() == conf.crote.alkyne() + 5


def test_type_name_list():
    assert type_name(List[int]) == 'List'


def test_type_name_dict():
    assert type_name(Dict[int, int]) == 'Dict'


def test_type_name_optional():
    assert type_name(Optional[int]) == 'Union'


def test_is_type_list():
    assert is_type(List[int])


def test_is_type_dict():
    assert is_type(Dict[int, int])


def test_is_type_optional():
    assert is_type(Optional[int])


def test_is_type_some_instance():
    assert not is_type(42)
    assert not is_type(object())


def test_is_type_some_type():
    class A:
        pass
    assert not is_type(A)
