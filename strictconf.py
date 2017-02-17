import sys
import typing
import codecs

from contextlib import contextmanager
from collections import namedtuple


PY3 = sys.version_info[0] == 3

if PY3:
    text_type = str

    def str_fix(s):
        return s

else:
    text_type = unicode  # noqa

    def str_fix(s):
        return text_type(s) if isinstance(s, str) else s


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(meta):

        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, 'temporary_class', (), {})


Context = namedtuple('Context', 'section key')

Error = namedtuple('Error', 'context message')


class ValidationError(TypeError):

    def __init__(self, message, errors):
        message += '\n' + '\n'.join(self._iter_errors(errors))
        super(ValidationError, self).__init__(message)

    def _iter_errors(self, errors):
        for error in errors:
            if error.context.key:
                ctx = '{}[{}]'.format(error.context.section, error.context.key)
            else:
                ctx = error.context.section or '<config>'
            yield ' - {} => {}'.format(ctx, error.message)


class Key(object):

    def __init__(self, name, type_):
        self.name = name
        self.type = type_


class NotInitialized(object):

    def __get__(self, instance, owner):
        raise RuntimeError('Config is not initialized')


class SectionBase(object):
    __keys__ = {}  # type: typing.Dict[str, Key]

    def __init__(self, name):
        self.__section_name__ = name


class SectionMeta(type):

    def __new__(mcs, name, bases, params):
        keys = {key: val for key, val in params.items()
                if isinstance(val, Key)}
        cls = super(SectionMeta, mcs).__new__(mcs, name, bases, params)
        cls.__keys__ = dict(cls.__keys__, **keys)

        not_initialized = NotInitialized()
        for attr_name in keys:
            setattr(cls, attr_name, not_initialized)

        return cls


class Section(with_metaclass(SectionMeta, SectionBase)):
    pass


class SectionValue(object):

    def __init__(self, section, value):
        for attr_name, key in section.__keys__.items():
            setattr(self, attr_name, value[key.name])


class ComposeBase(object):
    __sections__ = {}  # type: typing.Dict[str, Section]
    __initialized = False

    def __init_sections__(self, values):
        if self.__initialized:
            raise RuntimeError('Config is already initialized')
        for attr_name, section in self.__sections__.items():
            value = values[section.__section_name__]
            setattr(self, attr_name, SectionValue(section, value))
        self.__initialized = True


class ComposeMeta(type):

    def __new__(mcs, name, bases, params):
        sections = {key: val for key, val in params.items()
                    if isinstance(val, Section)}
        cls = super(ComposeMeta, mcs).__new__(mcs, name, bases, params)
        cls.__sections__ = dict(cls.__sections__, **sections)
        return cls


class Compose(with_metaclass(ComposeMeta, ComposeBase)):
    pass


def _type_params(type_):
    # Py3.4 typing module
    type_params = getattr(type_, '__args__', None)
    # Py3.5 typing module
    type_params = type_.__parameters__ if type_params is None else type_params
    return type_params


def _optional_type_param(type_):
    assert len(type_.__union_set_params__) == 2 and \
        type(None) in type_.__union_set_params__, \
        'Only "Optional" types are supported'
    return tuple(type_.__union_set_params__ - {type(None)})[0]


def _type_repr(t):
    if isinstance(t, typing.TypingMeta):
        if isinstance(t, typing.UnionMeta):
            optional_type_param = _optional_type_param(t)
            return 'Optional[{}]'.format(_type_repr(optional_type_param))
        else:
            params_repr = ', '.join(_type_repr(p) for p in _type_params(t))
            return '{}[{}]'.format(t.__name__, params_repr)
    else:
        return t.__name__


class TypeChecker(object):

    def __init__(self, ctx, value, errors):
        self.ctx = ctx
        self.stack = [value]
        self.errors = errors
        self.path = []

    def visit(self, type_):
        value = self.stack[-1]
        if not issubclass(type(value), type_):
            self.fail(type_, value)
        else:
            if isinstance(type_, typing.TypingMeta):
                method_name = 'visit_{}'.format(type_.__name__)
                visit_method = getattr(self, method_name, self.not_implemented)
                visit_method(type_, value)

    def not_implemented(self, type_, value):
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

    def visit_Union(self, type_, value):
        optional_type_param = _optional_type_param(type_)
        if value is not None:
            self.visit(optional_type_param)

    def visit_List(self, type_, value):
        item_type, = _type_params(type_)
        for i, item in enumerate(value):
            with self.push(item, '[{!r}]'.format(i)):
                self.visit(item_type)

    def visit_Dict(self, type_, value):
        key_type, val_type = _type_params(type_)
        for key, val in value.items():
            with self.push(key, '[{!r}]'.format(key)):
                self.visit(key_type)
            with self.push(val, '[{!r}]'.format(key)):
                self.visit(val_type)


def validate_type(ctx, value, type_, errors):
    if issubclass(type(value), type_):
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
        for key in obj.__keys__.values():
            ctx = Context(name, key.name)
            if key.name not in value:
                errors.append(Error(ctx, 'missing key'))
            else:
                key_value = value[key.name]
                validate_type(ctx, key_value, key.type, errors)


def validate_config(obj, value, variant, sep, errors):
    assert isinstance(obj, Compose), repr(type(obj))
    ctx = Context(None, None)
    validate_type(ctx, value, dict, errors)
    if errors:
        return

    key = text_type(sep.join(('compose', variant)))
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
        validate_type(ctx, str_fix(section_variant), text_type, errors)
        if errors:
            continue

        full_section_name = sep.join((section.__section_name__,
                                      section_variant))
        if full_section_name not in value:
            msg = '"{}" not found'.format(full_section_name)
            errors.append(Error(ctx, msg))
        else:
            section_value = value[full_section_name]
            validate_section(section, section_value, full_section_name, errors)


def validate(conf, data, variant, sep):
    errors = []
    validate_config(conf, data, variant, sep, errors)
    return errors


def compose(data, variant, sep):
    entrypoint = text_type(sep.join(('compose', variant)))
    compose_config = data[entrypoint]
    compose_result = {}
    for key, value in compose_config.items():
        section_name = sep.join((key, value))
        compose_result[key] = data[section_name]
    return compose_result


def init_from_data(conf, data, variant, sep='.'):
    errors = validate(conf, data, variant, sep)
    if errors:
        raise ValidationError('Configuration is not valid', errors)
    else:
        composed_data = compose(data, variant, sep)
        conf.__init_sections__(composed_data)


def init_from_toml(conf, file_name, variant, sep='_'):
    import toml  # type: ignore

    with codecs.open(file_name, encoding='utf-8') as f:
        content = f.read()
    data = toml.loads(content)
    init_from_data(conf, data, variant, sep=sep)


def init_from_yaml(conf, file_name, variant, sep='.'):
    import yaml  # type: ignore

    with codecs.open(file_name, encoding='utf-8') as f:
        content = f.read()
    data = yaml.load(content)
    init_from_data(conf, data, variant, sep=sep)
