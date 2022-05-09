import docker

from .frames import FrameController
from .templates import TemplateController
from .imka_configs import ImkaConfigController
from .stack import StackController
from .values import ValueController

class ImkaController:
    frameController: object
    valueController: object

    def __init__(self,):
        self.frameController = FrameController(
            TemplateController(),
            ImkaConfigController(docker.from_env(), TemplateController()),
            StackController(),
        )

        self.valueController = ValueController()

    def _init_frame(self, frame, version):
        self.frame = self.frameController.load_frame_from_uri(frame, version)

    def load_values(self, frame, deployment, value_files, render_values_depth, version):
        self._init_frame(frame, version)

        self.values = {
            'deployment': deployment,
            'deployment_fullname': '{}-{}'.format(self.frame.name, deployment)
        }

        self.imka_opts = {
            'render_values_depth': render_values_depth
        }

        self.values = self.valueController.load_values(self.frame, self.values, value_files, self.imka_opts)

        return self.values

    def render_templates(self, frame, deployment, value_files, render_values_depth, version):
        self.load_values(frame, deployment, value_files, render_values_depth, version)

        return self.frameController.evaluate_compose_yml(self.frame, self.values)

    def apply(self, frame, deployment, value_files, render_values_depth, version):
        self.load_values(frame, deployment, value_files, render_values_depth, version)
        return self.frameController.apply(self.frame, self.values)
        

    def down(self, frame, deployment, value_files, render_values_depth, version):
        self.load_values(frame, deployment, value_files, render_values_depth, version)
        self.frameController.down(self.values)