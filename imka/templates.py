import jinja2
import yaml

class TemplateController:
    def render_template(self, content, values):
        template = jinja2.Template(content)

        return template.render(values)

    def render_compose_templates(self, frame, values):
        rendered = []
        compose = {}

        for path in frame.get_compose_templates():
            with frame.fileProvider.open(path) as file:
                content = file.read()
            
            compose = self._merge_yaml(compose, yaml.safe_load(self.render_template(content, values)))

            rendered.append(path)

        frame.compose_yml = compose

        return rendered

    def _merge_yaml(self, destination, source):
        for key, value in source.items():
            if isinstance(value, dict) and value:
                node = destination.get(key, {})
                destination[key] = self._merge_yaml(node, value)
            else:
                destination[key] = value

        return destination