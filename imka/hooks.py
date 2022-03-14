import glob
import json
import subprocess
import sys

#import util

def run_hooks(context, name):
    for path in _find_hooks(context, name):
        _run_hook(context, path)

def run_values_hooks(context, name):
    for path in _find_hooks(context, name):
        path = _run_values_hook(context, path)
        context['values'] = util.merge_yaml(context['values'], path)

def _find_hooks(context, name):
    hooks = []
    for folder in context['hook_dirs']:
        hooks += glob.glob('{}/**/{}*'.format(folder, name), recursive=True)

    return hooks

def _run_hook(context, path):
    data = json.dumps(context['values'])
    subprocess.call([path, data], stderr=sys.stderr.buffer, stdout=sys.stdout.buffer)

def _run_values_hook(context, path):
    data = json.dumps(context['values'])
    out = subprocess.check_output([path, data])
    return json.loads(out)