import sys
import typing


PY37 = sys.version_info[:2] >= (3, 7)


if PY37:
    def is_type(obj):
        return isinstance(obj, typing._Final)
else:
    def is_type(obj):
        return (isinstance(obj, typing.TypingMeta)
                or isinstance(type(obj), typing.TypingMeta))


if PY37:
    def type_name(t):
        if t._name:
            return t._name
        else:
            return t.__origin__._name
else:
    def type_name(t):
        if isinstance(t, typing.TypingMeta):
            return t.__name__
        else:
            return type(t).__name__.lstrip('_')
