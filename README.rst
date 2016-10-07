StrictConf
==========

Define composable config:

.. code-block:: python

    from strictconf import Compose, Section, Key

    class Main(Section):
        foo = Key('foo', int)  # type: int

    class Config(Compose):
        main = Main('main')

    conf = Config()


Load using yaml format:

.. code-block:: python

    import yaml

    with open('config.yaml') as f:
        init(conf, 'default', yaml.load(f))

Or load using toml format:

.. code-block:: python

    import toml

    with open('config.toml') as f:
        init(conf, 'default', toml.load(f))

Or use any other suitable format.

Then use it in your application:

.. code-block:: python

    print(conf.main.foo + 1)

And be sure that "foo" key exists and it's type is "int".
