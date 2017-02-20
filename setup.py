import sys

from setuptools import setup, find_packages

PY35 = sys.version_info >= (3, 5)

setup(
    name='StrictConf',
    version='0.2.0',
    description='Configuration library with type-checking',
    author='Vladimir Magamedov',
    author_email='vladimir@magamedov.com',
    url='https://github.com/vmagamedov/strictconf',
    packages=find_packages(),
    install_requires=[] if PY35 else ['typing'],
    license='BSD',
)
