import yaml
import sys

from subprocess import Popen, PIPE, STDOUT

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