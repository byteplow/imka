import click
import yaml

from .imka import ImkaController

@click.group()
@click.pass_context
def main(ctx):
    ctx.obj = ImkaController()

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesting depth')
@click.option('--version', type=str, help='specify a frame version, only works for git: tag, branch or commit')
@click.pass_context
def values(ctx, frame, deployment, values, render_values_depth, version):
    dump = yaml.dump(ctx.obj.load_values(frame, deployment, values, render_values_depth, version))
    print('---')
    print(dump)

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesting depth')
@click.option('--version', type=str, help='specify a frame version, only works for git: tag, branch or commit')
@click.pass_context
def template(ctx, frame, deployment, values, render_values_depth, version):
    ctx.obj.render_templates(frame, deployment, values, render_values_depth, version)
    print('---')
    print(yaml.dump(ctx.obj.chart.compose_yml))

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesting depth')
@click.option('--version', type=str, help='specify a frame version, only works for git: tag, branch or commit')
@click.pass_context
def apply(ctx, frame, deployment, values, render_values_depth, version):
    ctx.obj.apply(frame, deployment, values, render_values_depth, version)

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesting depth')
@click.option('--version', type=str, help='specify a frame version, only works for git: tag, branch or commit')
@click.pass_context
def down(ctx, frame, deployment, values, render_values_depth, version):
    ctx.obj.down(frame, deployment, values, render_values_depth, version)