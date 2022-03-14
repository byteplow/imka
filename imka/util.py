import docker
import os

def open_with_context(context, path, mode='r'):
    return open(get_real_path(context, path), mode)

def get_real_path(context, path):
    return os.path.join(context['options']['frame_base_path'], path)

def merge_yaml(destination, source):
    for key, value in source.items():
        if isinstance(value, dict) and value:
            node = destination.get(key, {})
            destination[key] = merge_yaml(node, value)
        else:
            destination[key] = value

    return destination

def init_context():
    context = {}
    context['options'] = {}
    context['value_files'] = []
    context['values'] = {}
    context['configs'] = []
    context['mounts'] = []
    context['hook_dirs'] = []
    
    context['docker_client'] = docker.from_env()

    return context