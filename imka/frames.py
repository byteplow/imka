import yaml
from urllib.parse import urlparse

from .file_provider import FileProvider, GitFileProvider

COMPOSE_VERSION_POSTFIX = '-imka/v1'

class FrameController:
    templateController: object
    imkaConfigController: object
    stackController: object

    def __init__(self, templateController, imkaConfigController, stackController):
        self.templateController = templateController
        self.imkaConfigController = imkaConfigController
        self.stackController = stackController
        
    def load_frame_from_uri(self, frame_url, version):
        url = urlparse(frame_url)

        if url.scheme == '':
            fileProvider = FileProvider(frame_url)
        elif url.scheme in ['git+https', 'git+ssh', 'git+file']:
            fileProvider = GitFileProvider(frame_url, version)
        else:
            raise Exception("unknown url schema for frame")

        with fileProvider.open('frame.yml') as file:
            config = yaml.safe_load(file)

            compose_templates = config['compose_templates']
            name = config['name']

            valueFile = None
            if fileProvider.exists('values.yml'):
                valueFile = fileProvider.get_real_path('values.yml')

        return Frame(fileProvider, compose_templates, name, valueFile)

    def render_templates(self, frame, values):
        rendered = self.templateController.render_compose_templates(frame, values)

        for cfg in rendered:
            print('Rendering config {}'.format(cfg))

    def evaluate_compose_yml(self, frame, values):
        self.render_templates(frame, values)

        if not frame.compose_yml['version'].endswith(COMPOSE_VERSION_POSTFIX):
            raise Exception('compose version must end with {}'.format(COMPOSE_VERSION_POSTFIX))

        self.imkaConfigController.evaluate_compose_yml(frame, values)

        frame.compose_yml['version'] = frame.compose_yml['version'].replace(COMPOSE_VERSION_POSTFIX, '')

    def apply(self, frame, values):
        self.evaluate_compose_yml(frame, values)

        created = self.imkaConfigController.docker_create_configs(values)
        for cfg in created:
            print('Creating config {}'.format(cfg))

        self.stackController.apply(frame, values)

        deleted = self.imkaConfigController.docker_delete_old_config_versions()
        for cfg in deleted:
            print('Removing config {}'.format(cfg))

    def down(self, values):
        self.stackController.down(values)
        deleted = self.imkaConfigController.docker_delete_all_configs(values)

        for cfg in deleted:
            print('Removing config {}'.format(cfg))

    def dump(self, frame, values):
        """
        returns the spec for all running configs for this deployment - including standart docker config created by compose
        """
        self.evaluate_compose_yml(frame, values)

        configs = self.imkaConfigController.docker_dump_all_configs(values)
        service_image_map = self.stackController.get_service_image_map(values)

        self._repace_service_images_with_specif_versions(frame, service_image_map)

        return {
            'compose_yml': frame.compose_yml,
            'configs': configs
        }

    def _repace_service_images_with_specif_versions(self, frame, service_image_map):
        for serviceName, service in frame.compose_yml.get('services', {}).items():
            service['image'] = service_image_map[serviceName]
        

class Frame:
    fileProvider: None
    compose_yml: dict
    compose_templates: list
    value_file: str
    name: str

    def __init__(self, fileProvider, compose_templates, name, value_file):
        self.fileProvider = fileProvider
        self.compose_templates = compose_templates
        self.name = name
        self.value_file = value_file

    def get_compose_templates(self):
        paths = []

        for path in self.compose_templates:
            paths.append(path)

        return paths