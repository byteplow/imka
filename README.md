# IMKA - prototype-2
## package manager for docker swarm
Imka is a wrapper for docker stack. Imka reads values from multiple yaml files and merges them. The values then are use to render the docker compose templates. And finlay apply the result docker compose stack using "docker stack deploy".

In addition to values imka provides some function which can be used during templating.
Config functions wrap "docker configs" to add config content updates, jinja2 templating and directory configs (planed).
Mount functions provision an versions mount point for static files.

Imka calls hooks at different points in time, to executed custom scripts. There are 2 types of hooks. Rw-hooks can modify the values used for templating. Normal hooks can only consume the values.

## todo
- exception handling - currently the python an lib errors are shown - priority lowish
- config dirs - make configs from directories - priority high
- read frames from git repos - priority after high
- volume management - copy / move - priority not that high - maybe should be its own tool
- template value read and write to etcd - e.g service discovery between frame/clusters e.g. ingress network ... - dose it need it? - not that high > priority > lowish 

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
The compose templates are rendered and then merge. There fore the template done not need to be valid yaml.

There rendering context are the Values. They can be accessed like this: `{{key}}` `{{some_object.key_on_object}}`. Templates may also use expressions e.g if. See jinja2 documentation.

Templates can not use includes as every template is rendered on its own.

Imka provides functions which can be called in template like this. `{{imka.config_from_template('./some-file.j2')}}`

### Templating functions:
#### config_from_file()
Config_from_file return the name (as part of an config object) of a docker config. It is created by `imka apply` and delete by `imka down`.

The configs contains the contents of file at the given path. The file should be path of the frame. It is read on the imka executing system.

If the file or its path changes the config is updated. This will also update services, which are using this config (and are part of the deployment).

Internally: Docker configs can not be updated. A config is named by the file hash. If is changes a new config is created and the name is updated in the template.
`--prune-config-versions` deletes the old config version on apply.
The config paths is used as its id. Changing it will created dangling configs, they will be removed by `imka down`

#### signature
```
imka.config_from_file(path) return "{name: <config name>, external: true}"
```
#### example
```
version: '3.9'
services:
    my_services: 
        configs:
            - source: "my_config"
              target: "/some/other/dir"
configs:
    my_config: {{imka.config_from_file('./path/relative/to/frame.yml')}}  # must not be wrap in quotes
```
#### config_from_template()
The same as config_from_file, but before creating the config. The template is render with jinja2. The same rules apply as with compose templating
#### signature
```
imka.config_from_template(path) return "{name: <config name>, external: true}"
```
#### mount_from_dir()
Mount_from_dir returns the path to a copy of the dir. `imka apply` creates the copy and `imka down` deletes it. 

Mounts are also versioned like configs. Modifying the dir will create a new version and update the container (on apply).
`--prune-config-versions` will delete old mount versions on apply.

Mounts are provisioned by MountProvisioner. Currently there are LocalMountProvisioner and SshMountProvisioner. 
They can be configured in the imka config.

LocalMountProvisioner is for testing and single node use. It creates a versioned mount point in `local_mount_provisioner_base_path`.
It defaults to `./tmp/mounts`.

SshMountProvisioner copies the dirs to remotes systems using scp. It creates a versiond mount point on every hosted it `ssh_mount_provisioner_base_path`.
Hosts can be specified in `ssh_mount_provisioner_hosts`.

```
mount_provisioner: SshMountProvisioner
ssh_mount_provisioner_base_path: <path> # required
ssh_mount_provisioner_hosts: # at lease one host is needed
- hostname: <localhost> # required
  port: <22> # still required
  username: <user> # still required
```

#### signature
```
imka.config_from_file(path) return "{name: <config name>, external: true}"
```
#### example
```
version: '3.9'
services:
    my_services: 
        configs:
            - source: "my_config"
              target: "/some/other/dir"
configs:
    my_config: {{imka.config_from_file('./path/relative/to/frame.yml')}}  # must not be wrap in quotes
```

## Values.yml
Values can be read from multiple places. They are read in the following order from the frames values.yml, global values.yml and from yml specified as arguments. They are merged in the order they are read, where later keys overwrite earlier keys.

The merged values are rendered with jinja2. Every string may contain a jinja2 expression. They may be nested up to a depth of `--render-values-depth` (default: 32).

Values can also be modified by hooks. There are hooks which run `pre-values` which can set values be for loading the files. And hooks `post-values` which are run after rendering the values.

There are 3 predefined values 'deployment', 'deployment_fullname' and 'frame_name'. Changing them is possible, but my break some things.


((planed) Values can also be specified as arguments.)

Values can be show with `imka values`

## Hooks
Hooks may be used to modify values or run arbitrary code. They may be ued to load values from some datastore e.g. etcd or a vault. Or to update other systems e.g. dns entries.

Hooks are loaded from hook dirs. Hook dirs can be part of the frame or be specified as arguments or in the imka config. Hooks are loaded with the following glob `$hookdir/**/$hookname*`.

Hooks get passed the current values as json as first argument. RW-Hooks return json which is merge with the current values. Hooks may use values from previous hooks.

Theses hooks exists: 'pre-values', 'post-values', 'pre-apply', 'post-apply'

((planed) python lib for hooks functions, e.g. to store state in docker configs)

## Imka config
The imka config is located under `~/.config/d4rk.io/imka/config.yml`, but this can be overwritten with `--imka-config`.

`--imka-context` specifies the context to be used. The context can also be changed with `imka context use`

```
context: <context name> # the context from where config is loaded
contexts:
    <context name>:
        value_files: [<absolute paths>] # specify global value files
        hook_dirs: [<absolute paths>] # specify global hooks dirs
        options:
            mount_provisioner: SshMountProvisioner | LocalMountProvisioner # default: LocalMountProvisioner
            ssh_mount_provisioner_base_path: <path> # required
            local_mount_provisioner_base_path: <path> # optional
            ssh_mount_provisioner_hosts: # at lease one host is needed
              - hostname: <localhost> # required
                port: <22> # still required
                username: <user> # still required
    <second context name>:
```

## cli
FRAME path to frame directory
DEPLOYMENT deployment name

```
Usage: imka [OPTIONS] COMMAND [ARGS]...

Options:
  --imka-context TEXT  specify the imka config context
  --imka-config TEXT   specify the imka config path
  --help               Show this message and exit.

Commands:
  apply
  context
  down
  template
  values

Usage: imka apply [OPTIONS] FRAME DEPLOYMENT

Options:
  -f, --values PATH              specify values in YAML files to customize the
                                 frame deployment
  --render-values-depth INTEGER  specify the max allowed value template
                                 nesteding depth
  --prune-config-versions        specify that old config versions should be
                                 delete
  --prune-mount-versions         specify that old mount versions should be
                                 delete
  --help                         Show this message and exit.

Usage: imka context [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  list
  show
  use

Usage: imka down [OPTIONS] FRAME DEPLOYMENT

Options:
  -f, --values PATH              specify values in YAML files to customize the
                                 frame deployment
  --render-values-depth INTEGER  specify the max allowed value template
                                 nesteding depth
  --help                         Show this message and exit.

Usage: imka template [OPTIONS] FRAME DEPLOYMENT

Options:
  -f, --values PATH              specify values in YAML files to customize the
                                 frame deployment
  --render-values-depth INTEGER  specify the max allowed value template
                                 nesteding depth
  --help                         Show this message and exit.

Usage: imka values [OPTIONS] FRAME DEPLOYMENT

Options:
  -f, --values PATH              specify values in YAML files to customize the
                                 frame deployment
  --render-values-depth INTEGER  specify the max allowed value template
                                 nesteding depth
  --help                         Show this message and exit.
```

## Labels
todo ...