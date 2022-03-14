#!/usr/bin/env python3
import frontend
import util
import os
import click
import yaml
import hooks

@click.group()
@click.option('--imka-context', type=str, help='specify the imka config context')
@click.option('--imka-config', type=str, default=os.path.expanduser('~/.config/d4rk.io/imka/config.yml'), help='specify the imka config path')
@click.pass_context
def main(ctx, imka_context, imka_config):
    ctx.obj = util.init_context()

    ctx.obj['options']['imka_config'] = imka_config
    ctx.obj['options']['imka_context'] = imka_context

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesteding depth')
@click.pass_context
def values(ctx, frame, deployment, values, render_values_depth):
    _values(ctx, frame, deployment, values, render_values_depth)

    print(yaml.dump(ctx.obj['values']))

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesteding depth')
@click.pass_context
def template(ctx, frame, deployment, values, render_values_depth):
    _values(ctx, frame, deployment, values, render_values_depth)

    frontend.render_compose_templates(ctx.obj)

    print('---')
    print(yaml.dump(ctx.obj['docker_stack_yml']))

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesteding depth')
@click.option('--prune-config-versions', is_flag=True, help='specify that old config versions should be delete')
@click.option('--prune-mount-versions', is_flag=True, help='specify that old mount versions should be delete')
@click.pass_context
def apply(ctx, frame, deployment, values, render_values_depth, prune_config_versions, prune_mount_versions):
    _values(ctx, frame, deployment, values, render_values_depth)

    ctx.obj['options']['remove_old_config_versions_on_apply'] = prune_config_versions
    ctx.obj['options']['remove_old_mount_versions_on_apply'] = prune_mount_versions

    frontend.render_compose_templates(ctx.obj)

    hooks.run_hooks(ctx.obj, 'pre-apply')

    frontend.apply_configs(ctx.obj)
    frontend.apply_mounts(ctx.obj)

    frontend.stack_apply(ctx.obj)

    frontend.after_apply_configs(ctx.obj)
    frontend.after_apply_mounts(ctx.obj)

    hooks.run_hooks(ctx.obj, 'post-apply')

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesteding depth')
@click.pass_context
def down(ctx, frame, deployment, values, render_values_depth):
    _values(ctx, frame, deployment, values, render_values_depth)

    hooks.run_hooks(ctx.obj, 'pre-down')

    frontend.stack_down(ctx.obj)

    frontend.down_configs(ctx.obj)
    frontend.down_mounts(ctx.obj)

    hooks.run_hooks(ctx.obj, 'post-down')

@main.group()
def context():
    pass

@context.command(name='list')
@click.pass_context
def list_command(ctx):
    if os.path.exists(ctx.obj['options']['imka_config']):
        
        with open(ctx.obj['options']['imka_config']) as file:
            imkaConfig = yaml.safe_load(file)

        for key in imkaConfig['contexts'].keys():
            print(key)

@context.command(name='show')
@click.argument('context', type=str)
@click.pass_context
def context_show(ctx, context):
    if os.path.exists(ctx.obj['options']['imka_config']):
        with open(ctx.obj['options']['imka_config']) as file:
            imkaConfig = yaml.safe_load(file)

        if context in imkaConfig['contexts']:
            print(yaml.dump(imkaConfig['contexts'][context]))

@context.command()
@click.argument('context', type=str)
@click.pass_context
def use(ctx, context):
    if os.path.exists(ctx.obj['options']['imka_config']):
        with open(ctx.obj['options']['imka_config']) as file:
            imkaConfig = yaml.safe_load(file)

        if context not in imkaConfig['contexts']:
            print("error context dose not exist")
        
        imkaConfig['context'] = context

        with open(ctx.obj['options']['imka_config'], 'w') as file:
            file.write(yaml.dump(imkaConfig))

def _values(ctx, frame, deployment, values, render_values_depth):
    frontend.load_system_config(ctx.obj)

    ctx.obj['options']['frame'] = frame

    frontend.load_frame(ctx.obj)

    ctx.obj['values']['deployment'] = deployment
    ctx.obj['values']['deployment_fullname'] = '{}-{}'.format(ctx.obj['values']['frame_name'], ctx.obj['values']['deployment'])

    ctx.obj['options']['render_values_depth'] = render_values_depth
    ctx.obj['value_files'] += values

    hooks.run_values_hooks(ctx.obj, 'pre-values')

    frontend.load_values(ctx.obj)

    hooks.run_values_hooks(ctx.obj, 'post-values')

if __name__ == "__main__":
    main()