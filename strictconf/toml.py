from __future__ import absolute_import

import codecs

import toml

from . import data


def init(conf, file_names, variant, sep='_'):
    conf_data = {}
    for file_name in file_names:
        with codecs.open(file_name, encoding='utf-8') as f:
            conf_data.update(toml.loads(f.read()))
    data.init(conf, conf_data, variant, sep=sep)
