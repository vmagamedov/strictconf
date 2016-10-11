import sys
from setuptools import setup


PY35 = sys.version_info >= (3, 5)


setup(
    name='StrictConf',
    version='0.1.1',
    description='Configuration library with type-checking',
    author='Vladimir Magamedov',
    author_email='vladimir@magamedov.com',
    url='https://github.com/vmagamedov/strictconf',
    py_modules=['strictconf'],
    install_requires=[] if PY35 else ['typing'],
    license='BSD',
)
