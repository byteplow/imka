import jinja2
import yaml

from . import util

def load_values(context):
    read_from_files(context)
    render(context)

def read_from_files(context):
    values = context['values']

    for path in context['value_files']:
        with open(path) as file:
            current = yaml.safe_load(file)
        values = util.merge_yaml(values, current)

    context['values'] = values


def render(context):
    depth = context['options'].get('render_values_depth', 32)
    values = context['values']

    for i in range(depth):
        values = _render_values_step(values, values, i == depth-1)

    context['values'] = values

def _render_values_step(values, node, last):
    new = {}

    for key, value in node.items():
        if isinstance(value, dict) and value:
            new[key] = _render_values_step(values, value, last)
        elif isinstance(value, str):
            template = jinja2.Template(value)
            new[key] = template.render(values)

            if last and new[key].find('{{') >= 0:
                raise Exception('j2 templates could not be fully resolved!')
        else:
            new[key] = value

    return new