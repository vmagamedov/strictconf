import typing  # noqa

from .compat import with_metaclass, PY36


class Key(object):

    def __init__(self, name, type_):
        self.name = name
        self.type = type_


class NotInitialized(object):

    def __get__(self, instance, owner):
        raise RuntimeError('Config is not initialized')


class SectionBase(object):
    __keys__ = {}  # type: typing.Dict[str, Key]
    __descriptors__ = {}

    def __init__(self, name):
        self.__section_name__ = name


class SectionMeta(type):

    def __new__(mcs, name, bases, params):
        keys = {key: val for key, val in params.items()
                if isinstance(val, Key)}
        if PY36:
            annotations = params.get('__annotations__', {})
            for name, type_ in annotations.items():
                if name not in params:
                    keys.setdefault(name, Key(name, type_))

        descriptors = {key: val for key, val in params.items()
                       if getattr(val, '__get__', None) is not None}
        cls = super(SectionMeta, mcs).__new__(mcs, name, bases, params)
        cls.__keys__ = dict(cls.__keys__, **keys)
        cls.__descriptors__ = dict(cls.__descriptors__, **descriptors)

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
        self.__section = section
        self.__descriptors = section.__descriptors__

    def __getattr__(self, name):
        if name in self.__descriptors:
            value = self.__descriptors[name].__get__(self, self.__class__)
        else:
            value = getattr(self.__section, name)
        # caching
        setattr(self, name, value)
        return value


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
        if PY36:
            annotations = params.get('__annotations__', {})
            for name, section_type in annotations.items():
                if name not in params:
                    sections.setdefault(name, section_type(name))

        cls = super(ComposeMeta, mcs).__new__(mcs, name, bases, params)
        cls.__sections__ = dict(cls.__sections__, **sections)
        return cls


class Compose(with_metaclass(ComposeMeta, ComposeBase)):
    pass


class key_property(object):

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance.__dict__[self.func.__name__] = self.func(instance)
        return value
