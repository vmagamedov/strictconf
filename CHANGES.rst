Changelog
=========

0.3.0rc1
~~~~~~~~

- **BREAKING:** Dropped Python 3.5 and earlier versions support
- Added Python 3.7 version support

0.2.0
~~~~~

Backward-incompatible:

- Refactored project structure, import names were changed
- Changed signature of functions, used to init config from config files

New features:

- Added support for loading multiple configuration files
- Added ``key_property`` decorator to support computable values

0.1.2
~~~~~

New features:

- Added support for `typing.Optional` types validation

0.1.1
~~~~~

Fixes:

- Fixed unicode support in Python 2
