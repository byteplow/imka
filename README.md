# IMKA - prototype-2
## package manager for docker swarm
Imka is a wrapper for docker stack. Imka reads values from multiple yaml files and merges them. The values then are use to render the docker compose templates. And finlay apply the result docker compose stack using "docker stack deploy".

##### Features
+ multiple value files
+ docker compose templating with jinja2
+ docker config templating with jinja2
+ dirs as docker config
+ using frames in remote git repos

## todo
- exception handling - currently the python an lib errors are shown - priority lowish
- template value read and write to etcd - e.g service discovery between frame/clusters e.g. ingress network ... - dose it need it? - not that high > priority > lowish
- config support sort syntax
- dir templating white/blacklist
- supporting configs.configs
- secrets
- todo load values from remote servers repos

## Frame
An imka package is called a frame. It is a directory which must contain an frame.yml and one or more compose templates. It may also contain a values.yml, and a folder of hooks and arbitrary other files.
```
directory: <frame name>
    - hooks (optional directory)
    - frame.yml
    - values.yml (optional)
```

The frame.yml must contain the name of the frame and a list of compos templates.
```
name: <alpha numeric name, may contain a - >
compose_templates: <array of paths, relative to the frame.yml>
```

The hooks folder can contain executable hooks. They may be in subdirectories. See hooks.

## Compose templates
The compose templates are rendered and then merge. Therefor the template done not need to be valid yaml.

There rendering context are the Values. They can be accessed like this: `{{key}}` `{{some_object.key_on_object}}`. Templates may also use expressions e.g if. See jinja2 documentation.

Templates can not use includes as every template is rendered on its own.

### extension imka/v1
Imka currently only supports compose files with the extensions imka/v1. The version of there compose file needs to be `<compose_file_version-imka/v1>`

imka/v1 provides an extension for service configs in long syntax. (sort syntax is on the todo list).
```
version: "3.9"
services:
  redis:
    image: redis:latest
    deploy:
      replicas: 1
    configs:
      - type: imka
        source: path/to/node
        target: /redis_config
        uid: '103'
        gid: '103'
        mode: 0440
        template:
          enabled: true
```
`type: imka` must be set for imka to process this config.

`source` can now be a file or a directory. If source is a directory a config for any file in the directory and subdirectory is created.
The files are mounted at the target path `path/to/node/file1` get mounted at `/redis_config/file1`.

`template.enabled` enables imka jinja2 templating with the current values. For directory every file is templated.

`uid`, `gid`, `mode` work as defined.

## Values.yml
Values can be read from multiple places. They are read in the following order from the frames values.yml, global values.yml and from yml specified as arguments. They are merged in the order they are read, where later keys overwrite earlier keys.

The merged values are rendered with jinja2. Every string may contain a jinja2 expression. They may be nested up to a depth of `--render-values-depth` (default: 32).

Values can also be modified by hooks. There are hooks which run `pre-values` which can set values be for loading the files. And hooks `post-values` which are run after rendering the values.

There are 3 predefined values 'deployment', 'deployment_fullname' and 'frame_name'. Changing them is possible, but my break some things.


((planed) Values can also be specified as arguments.)

Values can be show with `imka values`

## Git
Frames can be retrieved from git. The frame name specified as following: `git+https://github.com/byteplow/imka.git#example/myframe`. Where `https://github.com/byteplow/imka.git` is a url pointing to a git repository. `example/myframe` is the frames path in the git repo. The frame path is optional. Imka supports `git+https`, `git+ssh` and `git+file`.

The cli option `..version` allows to set a git tag, commit or branch to be used. The default is main.

The repo are cached in `~/.cache/imka.d4rk.io`. There specific path is `~/.cache/imka.d4rk.io/sha[:2]/sha`m where `sha` is the sha256sum of the repo uri.

## cli
FRAME path to frame directory or git url 
DEPLOYMENT deployment name

```
Usage: imka [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  apply
  down
  template
  values


Usage: imka apply [OPTIONS] FRAME DEPLOYMENT

Options:
  -f, --values PATH              specify values in YAML files to customize the
                                 frame deployment
  --render-values-depth INTEGER  specify the max allowed value template
                                 nesting depth
  --version TEXT                 specify a frame version, only works for git:
                                 tag, branch or commit                
  --help                         Show this message and exit.


Usage: imka down [OPTIONS] FRAME DEPLOYMENT

Options:
  -f, --values PATH              specify values in YAML files to customize the
                                 frame deployment
  --render-values-depth INTEGER  specify the max allowed value template
                                 nesting depth
  --version TEXT                 specify a frame version, only works for git:
                                 tag, branch or commit
  --help                         Show this message and exit.


Usage: imka template [OPTIONS] FRAME DEPLOYMENT

Options:
  -f, --values PATH              specify values in YAML files to customize the
                                 frame deployment
  --render-values-depth INTEGER  specify the max allowed value template
                                 nesting depth
  --version TEXT                 specify a frame version, only works for git:
                                 tag, branch or commit
  --help                         Show this message and exit.


Usage: imka values [OPTIONS] FRAME DEPLOYMENT

Options:
  -f, --values PATH              specify values in YAML files to customize the
                                 frame deployment
  --render-values-depth INTEGER  specify the max allowed value template
                                 nesting depth
  --version TEXT                 specify a frame version, only works for git:
                                 tag, branch or commit
  --help                         Show this message and exit.
```

## Labels
### configs
+ `d4rk.io/imka/deployment`
+ `d4rk.io/imka/config/id` internal config id
+ `d4rk.io/imka/config/belongs_to` pointer to dir config id, if config is part of a directory