import hashlib
import docker

from . import util

from dataclasses import dataclass

@dataclass
class Config:
    configId: str
    version: str
    path: str
    docker_templating: bool
    content: str

    def apply(self, context):
        cli = context['docker_client']

        configs = cli.configs.list(filters={"name": self.version})

        if len(configs) == 0:
            return self.create(context)

        return False

    def create(self, context):
        cli = context['docker_client']

        if self.path:
            with util.open_with_context(context, self.path, 'rb') as file:
                data = file.read()

        if self.content:
            data = self.content.encode()

        labels = {
            'd4rk.io/imka/deployment': context['values']['deployment_fullname'],
            'd4rk.io/imka/config/id': self.configId,
        }

        templating = {}
        if self.docker_templating:
            templating = {
                'name': 'golang',
            }

        cli.configs.create(name=self.version, data=data, labels=labels, templating={})

        return self.version

    @staticmethod
    def down(context):
        cli = context['docker_client']

        configs = cli.configs.list(filters={"label": 'd4rk.io/imka/deployment={}'.format(context['values']['deployment_fullname'])})

        removed = []
        for config in configs:
            config.remove()
            removed.append(config.name)

        return removed

    def remove_old_versions(self, context):
        cli = context['docker_client']

        configs = cli.configs.list(filters={"label": 'd4rk.io/imka/config/id={}'.format(self.configId)})

        removed = []

        name = self.version
        for config in configs:
            if config.name != name:
                config.remove()
                removed.append(config.name)

        return removed

    @staticmethod
    def _get_id(context, path):
        localId = hashlib.sha256(path.encode()).hexdigest()[:32]

        return '{}-{}'.format(context['values']['deployment_fullname'], localId)

    @staticmethod
    def _get_version(context, path, config=None):
        if not config:
            with util.open_with_context(context, path) as file:
                config = file.read()

        return hashlib.sha256(config.encode()).hexdigest()

    @staticmethod
    def from_file(context, path, docker_templating):
        configId = Config._get_id(context, path)
        configVersion = Config._get_version(context, path)

        config = Config(configId, configVersion, path, docker_templating, None)
        context['configs'].append(config)

        return config

    @staticmethod
    def from_content(context, path, content):
        configId = Config._get_id(context, path)
        configVersion = Config._get_version(context, path, content)

        config = Config(configId, configVersion, None, False, content)
        context['configs'].append(config)

        return config

    @staticmethod
    def list(context):
        for config in context['configs'].values():
            print(config)

def apply_configs(context):
    for config in context['configs']:
        name = config.apply(context)
        if name:
            print('config {} created'.format(name))

def down_configs(context):
    removed = Config.down(context)
    for name in removed:
        print('config {} removed'.format(name))

def after_apply_configs(context):
    if context['options'].get('remove_old_config_versions_on_apply', False):
        for config in context['configs']:
            removed = config.remove_old_versions(context)
            for name in removed:
                print('config {} removed'.format(name))