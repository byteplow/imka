from dataclasses import dataclass
import hashlib
import os

CONFIG_TYPE = 'imka'
CONFIG_ID_LABEL = 'd4rk.io/imka/config/id'
CONFIG_BELONGS_TO_LABEL = 'd4rk.io/imka/config/belongs_to'
DEPLOYMENT_LABEL = 'd4rk.io/imka/deployment'

class ImkaConfigController:
    configs: list
    templateController = None
    dockerClient = None

    def __init__(self, dockerClient, templateController):
        self.configs = []
        self.dockerClient = dockerClient
        self.templateController = templateController

    def _add_config(self, frame, values, sourcePath, targetPath, imka_templating, mount_uid, mount_gid, mount_mode):
        if not frame.fileProvider.isdir(sourcePath):
            return [
                self._create_config(frame, values, sourcePath, targetPath, imka_templating, mount_uid, mount_gid, mount_mode, None)
            ]

        configId = self._generate_config_id(values, sourcePath)

        configs = []
        for path in frame.fileProvider.walk(sourcePath):
            pathRelativeToSource = os.path.relpath(path, sourcePath)
            mountPath = os.path.join(targetPath, pathRelativeToSource)

            config = self._create_config(frame, values, path, mountPath, imka_templating, mount_uid, mount_gid, mount_mode, configId)
            configs.append(config)

        return configs

    def _create_config(self, frame, values, sourcePath, targetPath, imka_templating, mount_uid, mount_gid, mount_mode, belongs_to):
        data = self._read_data(frame, values, sourcePath, imka_templating)

        config = ImkaConfig(
            self._generate_config_id(values, sourcePath),
            self._generate_version_id(data, values),
            targetPath,
            mount_uid,
            mount_gid,
            mount_mode,
            belongs_to,
            data
        )

        self.configs.append(config)

        return config

    def _read_data(self, frame, values, sourcePath, imka_templating):
        if imka_templating != True:
            with frame.fileProvider.open(sourcePath, 'rb') as file:
                return file.read()

        with frame.fileProvider.open(sourcePath) as file:
            content = file.read()

        rendered = self.templateController.render_template(content, values)
        return rendered.encode()

    def _generate_config_id(self, values, sourcePath):
        localId = hashlib.sha256(sourcePath.encode()).hexdigest()[:32]

        return '{}-{}'.format(values['deployment_fullname'], localId)

    def _generate_version_id(self, data, values):
        return hashlib.sha256(values['deployment_fullname'].encode() + data).hexdigest()

    # before apply
    def docker_create_configs(self, values):
        modified = []

        for config in self.configs:
            configs = self.dockerClient.configs.list(filters={"name": config.versionId})

            if len(configs) != 0:
                continue # config with this version already exists

            labels = {
                DEPLOYMENT_LABEL: values['deployment_fullname'], # use to delete all configs on down
                CONFIG_ID_LABEL: config.configId,
            }

            if config.belongs_to:
                labels[CONFIG_BELONGS_TO_LABEL] = config.belongs_to

            self.dockerClient.configs.create(name=config.versionId, data=config.data, labels=labels)

            modified.append(config.versionId)

        return modified

    # after apply
    def docker_delete_old_config_versions(self):
        modified = []

        for config in self.configs:
            configs = self.dockerClient.configs.list(filters={"label": '{}={}'.format(CONFIG_ID_LABEL, config.configId)})

            for live_config in configs:
                if live_config.name != config.versionId:
                    live_config.remove()
                    modified.append(live_config.name)

        return modified

    # down
    def docker_delete_all_configs(self, values):
        configs = self.dockerClient.configs.list(filters={"label": 'd4rk.io/imka/deployment={}'.format(values['deployment_fullname'])})

        removed = []
        for config in configs:
            config.remove()
            removed.append(config.name)

        return removed

    def evaluate_compose_yml(self, frame, values):
        if 'configs' not in frame.compose_yml:
            frame.compose_yml['configs'] = {}

        compose_configs = frame.compose_yml['configs']

        for serviceName, service in frame.compose_yml.get('services', {}).items():

            serviceConfigs = service.get('configs', [])

            for serviceConfigIndex in reversed(range(len(serviceConfigs))): # iterate list backwared, because items need to be inserted at the current index | is there a better way to do that in python?
                serviceConfig = serviceConfigs[serviceConfigIndex]
                if isinstance(serviceConfig, str) or serviceConfig.get('type', '') != CONFIG_TYPE:
                    continue

                sourcePath = serviceConfig.get('source', False)
                targetPath = serviceConfig.get('target', False)
                imka_templating = serviceConfig.get('template', {}).get('enabled', False)
                mount_uid = serviceConfig.get('uid', False)
                mount_gid = serviceConfig.get('gid', False)
                mount_mode = serviceConfig.get('mode', False)

                if not sourcePath:
                    raise Exception('services.{}.configs[{}].source must be set'.format(serviceName, serviceConfigIndex))

                if not targetPath:
                    raise Exception('services.{}.configs[{}].target must be set'.format(serviceName, serviceConfigIndex))

                configs = self._add_config(frame, values, sourcePath, targetPath, imka_templating, mount_uid, mount_gid, mount_mode)

                serviceConfigs.pop(serviceConfigIndex)

                for config in configs: # if configs need a specific order, the list needs to be reversed hear
                    serviceConfigs.insert(serviceConfigIndex, config.get_service_config_object())
                    compose_configs[config.configId] = config.get_config_object()


@dataclass
class ImkaConfig:
    """
    Represents a singe config object
    """
    configId: str # configId is used to identify a config independent of its version
    versionId: str # hash of templated file content
    targetPath: str
    mount_uid: str
    mount_gid: str
    mount_mode: int
    belongs_to: str # configId of parrent config if the source is a dir
    data: bytes

    def get_config_object(self):
        return {
            "external": True,
            "name": self.versionId
        }

    def get_service_config_object(self):
        return {
            "target": self.targetPath,
            "source": self.configId
            #todo mount opts
        }