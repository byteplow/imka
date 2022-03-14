import os
import yaml

import imka.frame
import imka.values

from . import imka_config
from . import hooks 
from . import templates
from . import configs
from . import mounts
from . import stack

def load_values(context, frame, deployment, values, render_values_depth):
    imka_config.load_system_config(context)

    context['options']['frame'] = frame

    imka.frame.load_frame(context)

    context['values']['deployment'] = deployment
    context['values']['deployment_fullname'] = '{}-{}'.format(context['values']['frame_name'], context['values']['deployment'])

    context['options']['render_values_depth'] = render_values_depth
    context['value_files'] += values

    hooks.run_values_hooks(context, 'pre-values')

    imka.values.load_values(context)

    hooks.run_values_hooks(context, 'post-values')

def render_templates(context, frame, deployment, values, render_values_depth):
    load_values(context, frame, deployment, values, render_values_depth)

    templates.render_compose_templates(context)

def apply(context, frame, deployment, values, render_values_depth, prune_config_versions, prune_mount_versions):
    context['options']['remove_old_config_versions_on_apply'] = prune_config_versions
    context['options']['remove_old_mount_versions_on_apply'] = prune_mount_versions

    render_templates(context, frame, deployment, values, render_values_depth)

    hooks.run_hooks(context, 'pre-apply')

    configs.apply_configs(context)
    mounts.apply_mounts(context)

    stack.stack_apply(context)

    configs.after_apply_configs(context)
    mounts.after_apply_mounts(context)

    hooks.run_hooks(context, 'post-apply')

def down(context, frame, deployment, values, render_values_depth):
    load_values(context, frame, deployment, values, render_values_depth)

    hooks.run_hooks(context, 'pre-down')

    stack.stack_down(context)

    configs.down_configs(context)
    mounts.down_mounts(context)

    hooks.run_hooks(context, 'post-down')

def context_list(context):
    if os.path.exists(context['options']['imka_config']):
        
        with open(context['options']['imka_config']) as file:
            imkaConfig = yaml.safe_load(file)

        for key in imkaConfig['contexts'].keys():
            print(key)

def context_show(context, name):
    if os.path.exists(context['options']['imka_config']):
        with open(context['options']['imka_config']) as file:
            imkaConfig = yaml.safe_load(file)

        if name in imkaConfig['contexts']:
            print(yaml.dump(imkaConfig['contexts'][name]))

def context_use(context, name):
    if os.path.exists(context['options']['imka_config']):
        with open(context['options']['imka_config']) as file:
            imkaConfig = yaml.safe_load(file)

        if name not in imkaConfig['contexts']:
            print("error context dose not exist")
        
        imkaConfig['context'] = name

        with open(context['options']['imka_config'], 'w') as file:
            file.write(yaml.dump(imkaConfig))