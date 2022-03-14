import jinja2
import json
import yaml
import copy

from . import util
from .configs import Config
from .mounts import Mount


class ImkaFunctions:
    def __init__(self, context):
        self.context = context

    def config_from_file(self, path, docker_templating=False):
        config = Config.from_file(self.context, path, docker_templating)

        return json.dumps({"external": True, "name": config.version})

    def config_from_template(self, path):
        with util.open_with_context(self.context, path) as file:
            template = file.read()

        content = render_template(self.context, template)

        config = Config.from_content(self.context, path, content)

        return json.dumps({"external": True, "name": config.version})

    def mount_dir(self, path):
        mount = Mount.from_path(self.context, path)

        return mount.mountPath


def render_template(context, content):
    j2context = copy.copy(context['values'])
    j2context['imka'] = ImkaFunctions(context)


    template = jinja2.Template(content)
    rendered = template.render(j2context)

    return yaml.safe_load(rendered)

def render_compose_templates(context):
    compose = {}

    for path in context['compose_templates']:
        with util.open_with_context(context, path) as file:
            content = file.read()
        
        compose = util.merge_yaml(compose, render_template(context, content))

        print('compose_template {} rendered'.format(path))

    context['docker_stack_yml'] = compose