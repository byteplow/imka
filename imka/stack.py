import yaml
import sys

from subprocess import Popen, PIPE, STDOUT

class StackController:
    def apply(self, frame, values):
        name = values['deployment_fullname']

        dockerStack = frame.compose_yml
        dockerStackYaml = yaml.dump(dockerStack)
        dockerStackYamlEncoded = dockerStackYaml.encode()

        p = Popen(['docker', 'stack', 'deploy', '-c', '-', name], stdin=PIPE, stderr=sys.stderr.buffer, stdout=sys.stdout.buffer)
        p.communicate(input=dockerStackYamlEncoded)[0]

    def down(self, values):
        name = values['deployment_fullname']

        p = Popen(['docker', 'stack', 'rm', name], stderr=sys.stderr.buffer, stdout=sys.stdout.buffer)
        p.communicate()[0]