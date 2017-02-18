from .compat import text_type


def compose(data, variant, sep):
    entrypoint = text_type(sep.join(('compose', variant)))
    compose_config = data[entrypoint]
    compose_result = {}
    for key, value in compose_config.items():
        section_name = sep.join((key, value))
        compose_result[key] = data[section_name]
    return compose_result
