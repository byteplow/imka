import os
import yaml

from . import util

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
