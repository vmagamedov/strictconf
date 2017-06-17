import sys

PY3 = sys.version_info > (3, 0)
PY36 = sys.version_info[:2] >= (3, 6)

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
