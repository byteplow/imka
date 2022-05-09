import jinja2
import yaml

class ValueController:
    def load_values(self, frame, values, value_files, imka_opts):
        if frame.value_file:
            value_files = [frame.value_file] + list(value_files)

        for path in value_files:
            with open(path) as file:
                current = yaml.safe_load(file)
            values = self._merge_yaml(values, current)

        depth = imka_opts.get('render_values_depth', 32)
        for i in range(depth):
            values = self._render_values(values, values, i == depth-1)

        return values

    def _render_values(self, values, node, last):
        new = {}

        for key, value in node.items():
            if isinstance(value, dict) and value:
                new[key] = self._render_values(values, value, last)
            elif isinstance(value, str):
                template = jinja2.Template(value)
                new[key] = template.render(values)

                if last and new[key].find('{{') >= 0:
                    raise Exception('j2 templates could not be fully resolved!')
            else:
                new[key] = value

        return new

    def _merge_yaml(self, destination, source):
        for key, value in source.items():
            if isinstance(value, dict) and value:
                node = destination.get(key, {})
                destination[key] = self._merge_yaml(node, value)
            else:
                destination[key] = value

        return destination