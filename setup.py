from setuptools import setup

setup(
    name='imka',
    version='0.1.0',    
    description='A docker swarm package manager',
    url='https://github.com/byteplow/imka',
    author='byteplow',
    author_email='byteplow@posteo.de',
    license='MIT License',
    packages=['imka'],
    scripts=['command/imka'],
    install_requires=[
        'click',
        'dirhash',
        'docker',
        'Jinja2',
        'pyaml',
        'scp',
        'paramiko', 
    ],
    project_urls={
        'Source': 'https://github.com/byteplow/imka',
    },
)