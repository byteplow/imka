from templates import render_template
import util
import values
import os
import yaml
from subprocess import Popen, PIPE, STDOUT
import sys
from configs import Config
from mounts import Mount

def load_values(context):
    values.read_from_files(context)
    values.render(context)

def render_compose_templates(context):
    compose = {}

    for path in context['compose_templates']:
        with util.open_with_context(context, path) as file:
            content = file.read()
        
        compose = util.merge_yaml(compose, render_template(context, content))

        print('compose_template {} rendered'.format(path))

    context['docker_stack_yml'] = compose

def apply_configs(context):
    for config in context['configs']:
        name = config.apply(context)
        if name:
            print('config {} created'.format(name))

def apply_mounts(context):
    for mount in context['mounts']:
        names = mount.apply(context)
        for name in names:
            print('mount {} created'.format(name))

def after_apply_configs(context):
    if context['options'].get('remove_old_config_versions_on_apply', False):
        for config in context['configs']:
            removed = config.remove_old_versions(context)
            for name in removed:
                print('config {} removed'.format(name))

def after_apply_mounts(context):
    if context['options'].get('remove_old_mount_versions_on_apply', False):
        for mount in context['mounts']:
            removed = mount.remove_old_versions(context)
            for name in removed:
                print('mount {} removed'.format(name)) 

def down_configs(context):
    removed = Config.down(context)
    for name in removed:
        print('config {} removed'.format(name))

def down_mounts(context):
    removed = Mount.down(context)
    for name in removed:
        print('mount {} removed'.format(name))

def load_system_config(context):
    if os.path.exists(context['options']['imka_config']):
        with open(context['options']['imka_config']) as file:
            imkaConfig = yaml.safe_load(file)

        if not context['options']['imka_context']:
            context['options']['imka_context'] = imkaConfig['context']

        config = imkaConfig['contexts'][context['options']['imka_context']]

        context['value_files'] = config.get('value_files', [])
        context['hook_dirs'] = config.get('hook_dirs', [])

        context['options'] = config['options']

def load_frame(context):
    context['options']['frame_base_path'] = os.path.abspath(context['options']['frame'])

    with util.open_with_context(context, './frame.yml') as file:
        frameConfig = yaml.safe_load(file)

    context['values']['frame_name'] = frameConfig['name']
    context['compose_templates'] = frameConfig['compose_templates']

    valueFiles = os.path.join(context['options']['frame_base_path'], 'values.yml')
    if (os.path.exists(valueFiles)):
        context['value_files'] = [valueFiles] + context['value_files']

    hookDir = os.path.join(context['options']['frame_base_path'], 'hooks')
    if (os.path.exists(hookDir)):
        context['hook_dirs'] = [hookDir] + context['hook_dirs']

def stack_apply(context):
    name = context['values']['deployment_fullname']

    dockerStack = context['docker_stack_yml']
    dockerStackYaml = yaml.dump(dockerStack)
    dockerStackYamlEncoded = dockerStackYaml.encode()

    p = Popen(['docker', 'stack', 'deploy', '-c', '-', name], stdin=PIPE, stderr=sys.stderr.buffer, stdout=sys.stdout.buffer)
    p.communicate(input=dockerStackYamlEncoded)[0]

def stack_down(context):
    name = context['values']['deployment_fullname']

    p = Popen(['docker', 'stack', 'rm', name], stderr=sys.stderr.buffer, stdout=sys.stdout.buffer)
    p.communicate()[0]