import codecs
import typing
from collections import namedtuple

import collections


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(meta):

        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, 'temporary_class', (), {})


class NotInitialized(object):

    def __get__(self, instance, owner):
        raise RuntimeError('Config is not initialized')


Context = namedtuple('Context', 'section key')

Error = namedtuple('Error', 'context message')


class Key(object):

    def __init__(self, name, type_):
        self.name = name
        self.type = type_


class SectionObject(object):
    pass


class SectionBase(object):
    __section_keys__ = {}

    def __init__(self, name):
        self.__section_name__ = name


class SectionMeta(type):

    def __new__(mcs, name, bases, params):
        cls = super(SectionMeta, mcs).__new__(mcs, name, bases, params)
        keys = cls.__section_keys__.copy()
        for name, value in params.items():
            if isinstance(value, Key):
                keys[name] = value
        cls.__section_keys__ = keys
        return cls


class Section(with_metaclass(SectionMeta, SectionBase)):
    pass


class ComposeBase(object):
    __sections__ = {}


class ComposeMeta(type):

    def __new__(mcs, name, bases, params):
        cls = super(ComposeMeta, mcs).__new__(mcs, name, bases, params)
        sections = cls.__sections__.copy()
        for name, value in params.items():
            if isinstance(value, Section):
                sections[name] = value
        cls.__sections__ = sections
        return cls


class Compose(with_metaclass(ComposeMeta, ComposeBase)):
    pass


class TypeChecker(object):

    def __init__(self, value):
        self.stack = [value]
        self.path = []

    def visit(self, type_):
        assert isinstance(type_, typing.TypingMeta)
        method_name = 'visit_{}'.format(type_.__name__)
        getattr(self, method_name, self.visit_unknown)(type_)

    def visit_unknown(self, type_):
        raise TypeError('Type check is not implemented for this type: {!r}'
                        .format(type_))

    def fail(self, type_):
        pass

    def visit_List(self, type_):
        value = self.stack[-1]
        if not isinstance(value, type_):
            return self.fail(type_)

        item_type, = type_.__parameters__
        for i, item in enumerate(value):
            self.path.append('[{}]'.format(i))
            self.stack.append(item)
            try:
                self.visit(item_type)
            finally:
                self.path.pop()
                self.stack.pop()


def _validate_type(ctx, value, type_, errors):
    if isinstance(value, type_):
        if isinstance(type_, typing.TypingMeta):
            raise NotImplementedError
        return

    left, right = type(value).__name__, type_.__name__
    message = '"{}" instead of "{}"'.format(left, right)
    errors.append(Error(ctx, message))


def _validate_section(obj, value, name, errors):
    assert isinstance(obj, Section), repr(type(obj))
    ctx = Context(name, None)
    _validate_type(ctx, value, dict, errors)
    if not errors:
        for key in obj.__section_keys__.values():
            ctx = Context(name, key.name)
            if key.name not in value:
                errors.append(Error(ctx, 'missing key'))
            else:
                key_value = value[key.name]
                _validate_type(ctx, key_value, key.type, errors)


def _validate_config(obj, value, variant, errors):
    assert isinstance(obj, Compose), repr(type(obj))
    ctx = Context(None, None)
    _validate_type(ctx, value, dict, errors)
    if not errors:
        key = 'compose.{}'.format(variant)
        if key not in value:
            errors.append(Error(Context(key, None), 'missing section'))
        else:
            ctx = Context(key, None)
            compose_section = value[key]
            _validate_type(ctx, compose_section, dict, errors)
            if not errors:
                for section in obj.__sections__.values():
                    ctx = Context(key, section.__section_name__)
                    if section.__section_name__ not in compose_section:
                        errors.append(Error(ctx, 'missing key'))
                    else:
                        section_variant = compose_section[section.__section_name__]
                        _validate_type(ctx, section_variant, str, errors)
                        if not errors:
                            full_section_name = '.'.join((section.__section_name__,
                                                          section_variant))
                            if full_section_name not in value:
                                msg = '"{}" not found'.format(full_section_name)
                                errors.append(Error(ctx, msg))
                            else:
                                section_value = value[full_section_name]
                                _validate_section(section, section_value, full_section_name, errors)


def validate(conf, data, variant):
    errors = []
    _validate_config(conf, data, variant, errors)
    return errors


def compose(data, variant):
    entrypoint = 'compose.{}'.format(variant)
    compose_config = data[entrypoint]
    compose_result = {}
    for key, value in compose_config.items():
        section_name = '{}.{}'.format(key, value)
        compose_result[key] = data[section_name]
    return compose_result


# def init(conf, variant, data):
#     composed_data = compose(data, variant)
#     errors = validate(conf, composed_data)
#     if errors:
#         raise TypeError(repr(errors))  # FIXME
#     else:
#         conf.__data__ = compose(data, variant)


def read_toml(file_name, variant):
    import toml

    with codecs.open(file_name, 'rb', 'utf-8') as f:
        content = f.read()
    data = toml.loads(content)
    return compose(data, variant)


def read_yaml(file_name, variant):
    import yaml

    with codecs.open(file_name, 'rb', 'utf-8') as f:
        content = f.read()
    data = yaml.load(content)
    return compose(data, variant)
