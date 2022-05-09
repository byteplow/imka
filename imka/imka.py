class ImkaController:
    frameController: object
    valueController: object

    def __init__(self, frameController, valueController):
        self.frameController = frameController
        self.valueController = valueController

    def load_values(self, frame, deployment, value_files, render_values_depth):
        self.frame = self.frameController.load_frame_from_uri(frame)

        self.values = {
            'deployment': deployment,
            'deployment_fullname': '{}-{}'.format(self.frame.name, deployment)
        }

        self.imka_opts = {
            'render_values_depth': render_values_depth
        }

        self.values = self.valueController.load_values(self.frame, self.values, value_files, self.imka_opts)

        return self.values

    def render_templates(self, frame, deployment, value_files, render_values_depth):
        self.load_values(frame, deployment, value_files, render_values_depth)

        return self.frameController.evaluate_compose_yml(self.frame, self.values)

    def apply(self, frame, deployment, value_files, render_values_depth):
        self.load_values(frame, deployment, value_files, render_values_depth)
        return self.frameController.apply(self.frame, self.values)
        

    def down(self, frame, deployment, value_files, render_values_depth):
        self.load_values(frame, deployment, value_files, render_values_depth)
        self.frameController.down(self.values)