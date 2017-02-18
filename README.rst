StrictConf
==========

Configuration library with type-checking and composition instead of inheritance

Install:

.. code-block:: shell

  $ pip install strictconf


Config definition
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from strictconf import Compose, Section, Key

    class Main(Section):
        hours = Key('hours', int)  # type: int

    class Config(Compose):
        main = Main('main')

    conf = Config()


Init using yaml_ format
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    main.earth:
      hours: 24

    compose.default:
      main: earth

.. code-block:: python

    from strictconf.yaml import init

    init(conf, ['config.yaml'], 'default')


Init using toml_ format
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: toml

    [main_earth]
    hours = 24

    [compose_default]
    main = "earth"

.. code-block:: python

    from strictconf.toml import init

    init(conf, ['config.toml'], 'default')


Init using plain data
~~~~~~~~~~~~~~~~~~~~~

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

And be sure that "hours" key exists and it's type is ``int``.

.. _yaml: http://yaml.org
.. _toml: https://github.com/toml-lang/toml
