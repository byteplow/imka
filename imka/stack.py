import yaml
import sys

from subprocess import Popen, PIPE, STDOUT

class StackController:
    dockerClient: object

    def __init__(self, dockerClient):
        self.dockerClient = dockerClient

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

    def get_service_image_map(self, values):
        results = {}
        services = self.dockerClient.services.list(filters={"label": 'com.docker.stack.namespace={}'.format(values['deployment_fullname'])})

        for service in services:
            image = service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image']
            name = service.name.replace(values['deployment_fullname'] + '_', '', 1)

            results[name] = image

        return results

