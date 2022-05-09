import click
import yaml
import docker

from .imka import ImkaController
from .frames import FrameController
from .templates import TemplateController
from .imka_configs import ImkaConfigController
from .stack import StackController
from .values import ValueController


@click.group()
@click.pass_context
def main(ctx):
    ctx.obj = ImkaController(
        FrameController(
            TemplateController(),
            ImkaConfigController(docker.from_env(), TemplateController()),
            StackController(),
        ),
        ValueController()
    )

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesteding depth')
@click.pass_context
def values(ctx, frame, deployment, values, render_values_depth):
    dump = yaml.dump(ctx.obj.load_values(frame, deployment, values, render_values_depth))
    print('---')
    print(dump)

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesteding depth')
@click.pass_context
def template(ctx, frame, deployment, values, render_values_depth):
    rendered = ctx.obj.render_templates(frame, deployment, values, render_values_depth)

    print('---')
    print(yaml.dump(ctx.obj.chart.compose_yml))

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesteding depth')
@click.pass_context
def apply(ctx, frame, deployment, values, render_values_depth):
    ctx.obj.apply(frame, deployment, values, render_values_depth)

@main.command()
@click.argument('frame', type=str)
@click.argument('deployment', type=str)
@click.option('--values', '-f', multiple=True, type=click.Path(exists=True), help='specify values in YAML files to customize the frame deployment')
@click.option('--render-values-depth', type=int, default=32, help='specify the max allowed value template nesteding depth')
@click.pass_context
def down(ctx, frame, deployment, values, render_values_depth):
    ctx.obj.down(frame, deployment, values, render_values_depth)