import click
import yaml
import os

import imka

@click.group()
@click.option('--imka-context', type=str, help='specify the imka config context')
@click.option('--imka-config', type=str, default=os.path.expanduser('~/.config/d4rk.io/imka/config.yml'), help='specify the imka config path')
@click.pass_context
def main(ctx, imka_context, imka_config):
    ctx.obj = imka.init_context()

    ctx.obj['options']['imka_config'] = imka_config
    ctx.obj['options']['imka_context'] = imka_context

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesteding depth')
@click.pass_context
def values(ctx, frame, deployment, values, render_values_depth):
    imka.load_values(ctx.obj, frame, deployment, values, render_values_depth)

    print(yaml.dump(ctx.obj['values']))

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesteding depth')
@click.pass_context
def template(ctx, frame, deployment, values, render_values_depth):
    imka.render_templates(ctx.obj, frame, deployment, values, render_values_depth)

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
    imka.apply(ctx.obj, frame, deployment, values, render_values_depth, prune_config_versions, prune_mount_versions)

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesteding depth')
@click.pass_context
def down(ctx, frame, deployment, values, render_values_depth):
    imka.down(ctx.obj, frame, deployment, values, render_values_depth)

@main.group()
def context():
    pass

@context.command(name='list')
@click.pass_context
def list_command(ctx):
    imka.context_list(ctx.obj)

@context.command(name='show')
@click.argument('context', type=str)
@click.pass_context
def context_show(ctx, context):
    imka.context_show(ctx.obj, context)

@context.command()
@click.argument('context', type=str)
@click.pass_context
def use(ctx, context):
    imka.context_use(ctx.obj, context)