import typing  # noqa

from .compat import with_metaclass


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
