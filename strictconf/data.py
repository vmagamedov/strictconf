from .compose import compose
from .checker import validate, ValidationError


def init(conf, data, variant, sep='.'):
    errors = validate(conf, data, variant, sep)
    if errors:
        raise ValidationError('Configuration is not valid', errors)
    else:
        composed_data = compose(data, variant, sep)
        conf.__init_sections__(composed_data)
