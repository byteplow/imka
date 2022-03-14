import os
import yaml

def load_system_config(context):
    if os.path.exists(context['options']['imka_config']):
        with open(context['options']['imka_config']) as file:
            imkaConfig = yaml.safe_load(file)

        if not context['options']['imka_context']:
            context['options']['imka_context'] = imkaConfig['context']

        config = imkaConfig['contexts'][context['options']['imka_context']]

        context['value_files'] = config.get('value_files', [])
        context['hook_dirs'] = config.get('hook_dirs', [])

        context['options'] = config['options']