import typing
import codecs

from contextlib import contextmanager
from collections import namedtuple


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


def _params(type_, default=None):
    return getattr(type_, '__args__', getattr(type_, '__parameters__', default))


class TypeChecker(object):

    def __init__(self, ctx, value, errors):
        self.ctx = ctx
        self.stack = [value]
        self.errors = errors
        self.path = []

    def visit(self, type_):
        value = self.stack[-1]
        if not isinstance(value, type_):
            self.fail(type_, value)
        else:
            if isinstance(type_, typing.TypingMeta):
                method_name = 'visit_{}'.format(type_.__name__)
                visit_method = getattr(self, method_name, self.not_implemented)
                visit_method(type_, value)

    def not_implemented(self, type_):
        raise TypeError('Type check is not implemented for this type: {!r}'
                        .format(type_))

    @contextmanager
    def push(self, value, path_element):
        self.path.append(path_element)
        self.stack.append(value)
        try:
            yield
        finally:
            self.path.pop()
            self.stack.pop()

    def fail(self, type_, value):
        provided = _type_repr(type(value))
        expected = _type_repr(type_)
        msg = '"{}" instead of "{}"'.format(provided, expected)
        if self.path:
            msg = '{} - {}'.format(''.join(self.path), msg)
        self.errors.append(Error(self.ctx, msg))

    def visit_List(self, type_, value):
        item_type, = _params(type_)
        for i, item in enumerate(value):
            with self.push(item, '[{!r}]'.format(i)):
                self.visit(item_type)

    def visit_Dict(self, type_, value):
        key_type, val_type = _params(type_)
        for key, val in value.items():
            with self.push(key, '[{!r}]'.format(key)):
                self.visit(key_type)
            with self.push(val, '[{!r}]'.format(key)):
                self.visit(val_type)


def _type_repr(t):
    params = _params(t)
    if params is not None:
        params_repr = ', '.join(_type_repr(p) for p in params)
        return '{}[{}]'.format(t.__name__, params_repr)
    else:
        return t.__name__


def validate_type(ctx, value, type_, errors):
    if isinstance(value, type_):
        if isinstance(type_, typing.TypingMeta):
            TypeChecker(ctx, value, errors).visit(type_)
        return
    else:
        message = ('"{}" instead of "{}"'
                   .format(_type_repr(type(value)), _type_repr(type_)))
        errors.append(Error(ctx, message))


def validate_section(obj, value, name, errors):
    assert isinstance(obj, Section), repr(type(obj))
    ctx = Context(name, None)
    validate_type(ctx, value, dict, errors)
    if not errors:
        for key in obj.__section_keys__.values():
            ctx = Context(name, key.name)
            if key.name not in value:
                errors.append(Error(ctx, 'missing key'))
            else:
                key_value = value[key.name]
                validate_type(ctx, key_value, key.type, errors)


def validate_config(obj, value, variant, errors):
    assert isinstance(obj, Compose), repr(type(obj))
    ctx = Context(None, None)
    validate_type(ctx, value, dict, errors)
    if errors:
        return

    key = 'compose.{}'.format(variant)
    if key not in value:
        errors.append(Error(Context(key, None), 'missing section'))
        return

    ctx = Context(key, None)
    compose_section = value[key]
    validate_type(ctx, compose_section, dict, errors)
    if errors:
        return

    for section in obj.__sections__.values():
        ctx = Context(key, section.__section_name__)
        if section.__section_name__ not in compose_section:
            errors.append(Error(ctx, 'missing key'))
            continue

        section_variant = compose_section[section.__section_name__]
        validate_type(ctx, section_variant, str, errors)
        if errors:
            continue

        full_section_name = '.'.join((section.__section_name__,
                                      section_variant))
        if full_section_name not in value:
            msg = '"{}" not found'.format(full_section_name)
            errors.append(Error(ctx, msg))
        else:
            section_value = value[full_section_name]
            validate_section(section, section_value, full_section_name, errors)


def validate(conf, data, variant):
    errors = []
    validate_config(conf, data, variant, errors)
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
