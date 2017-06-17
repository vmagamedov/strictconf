``strictconf`` version ``0.2.0``

Configuration library with type-checking and composition instead of inheritance

.. code-block:: shell

  $ pip install strictconf


Config definition
~~~~~~~~~~~~~~~~~

In Python < 3.6:

.. code-block:: python

    from strictconf import Compose, Section, Key

    class Main(Section):
        hours = Key('hours', int)

    class Config(Compose):
        main = Main('main')

    conf = Config()

In Python >= 3.6:

.. code-block:: python

    from strictconf import Compose, Section

    class Main(Section):
        hours: int

    class Config(Compose):
        main: Main

    conf = Config()

Initialize using yaml_ format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    main.earth:
      hours: 24

    compose.default:
      main: earth

.. code-block:: python

    from strictconf.yaml import init

    init(conf, ['config.yaml'], 'default')


Initialize using toml_ format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: toml

    [main_earth]
    hours = 24

    [compose_default]
    main = "earth"

.. code-block:: python

    from strictconf.toml import init

    init(conf, ['config.toml'], 'default')


Initialize using plain data
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from strictconf.data import init

    data = {
        'main.earth': {
            'hours': 24,
        },
        'compose.default': {
            'main': 'earth',
        },
    }

    init(conf, data, 'default')


Config usage
~~~~~~~~~~~~

.. code-block:: python

    >>> print('Seconds: {}'.format(conf.main.hours * 60 * 60))
    Seconds: 86400

And be sure that ``hours`` key exists and it's type is ``int``.

Key types
~~~~~~~~~

``strictconf`` uses Python's standard ``typing`` module to describe complex key
types. Examples:

.. code-block:: python

    from typing import Optional, List, Dict

    class MySection(Section):
        foo = Key('foo', Optional[int])
        bar = Key('bar', List[int])
        baz = Key('baz', Dict[str, int])

        bazinga = Key('bazinga', List[Dict[str, Optional[int]]])

**Note**: ``typing`` and types in Python are very complex and ``strictconf``
implements only basic type checking, so if key type is not supported by
``strictconf``, it will raise ``NotImplementedError`` with explanation.

Config layout
~~~~~~~~~~~~~

With ``strictconf`` it is possible to place all configuration for all
environments into single file. But for especially big projects this file
wouldn't be easy to maintain. In order to overcome this issue ``strictconf``
allows you to load config from several files:

.. code-block:: python

    init(conf, ['foo.yaml', 'bar.yaml', 'baz.yaml', 'compose.yaml'], 'default')

``strictconf`` will merge content of these files into one namespace and check it
as it was one file. Good news is that this approach is dead easy. Bad
news is that you can not dynamically reference external files to load from
config itself, you should specify all files explicitly on config initialization.

**Note**: each next file in the list of files can overwrite/override sections
from previous files. This bug or feature was not desired, just take a note, that
normally you don't need to override anything, use composition instead for a
great good!

How to split config into multiple files? – There are one rule of thumb: split
config with file per section::

    foo.yaml bar.yaml baz.yaml compose.yaml

Where ``foo.yaml`` will contain all ``foo`` section variations. As a bonus, you
will be able to use yaml_ anchors to avoid values duplication even more.

**Note**: ``strictconf`` is designed to reduce duplication by using sections
composition, so you will be good with any file format, yaml_ just gives you
slightly more features and expressiveness.

And you will have main ``compose.yaml`` configuration file, where sections from
other files will be composed into final configurations.

Computable config values
~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, when working with configuration values, you will need to transform
raw config values into more high-level values for use in your application's
code.

One of these examples are ``enum`` values:

.. code-block:: python

    class Color(Enum):
        blue = 'BLUE'
        gray = 'GRAY'

For example, configuration will be looking like this:

.. code-block:: python

    class Style(Section):
        color = Key('color', str)

    class Config(Compose):
        style = Style('style')

    conf = Config()

.. code-block:: yaml

    style.dark:
      color: GRAY

    compose.default:
      style: dark

And instead of converting config's color into enum's color every single time:

.. code-block:: python

    assert Color(conf.style.color) is Color.gray

You can instead do this:

.. code-block:: python

    from strictconf import key_property

    class Style(Section):
        _color = Key('color', str)

        @key_property
        def color(self):
            return Color(self._color)

    ...

    assert conf.style.color is Color.gray

``Style.color`` method will be called only once and it's value will be cached.
Next time you will access this computed value as normal attribute with no
additional cost.

You can also specify ``key_property`` in ``Config`` class (your ``Compose``
subclass), where you will be able to read config values from any section to
perform more complex computations.

.. _yaml: http://yaml.org
.. _toml: https://github.com/toml-lang/toml
