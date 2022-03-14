import os
import hashlib
import shutil

from . import util

from dirhash import dirhash
from dataclasses import dataclass
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

@dataclass
class Mount:
    mountId: str
    version: str
    path: str
    mountPath: str
    deployment: str

    def apply(self, context):
        provisioner = get_mount_provisioner(context)

        return provisioner.apply(context, self)

    @staticmethod
    def down(context):
        deployment = context['values']['deployment_fullname']
        provisioner = get_mount_provisioner(context)

        return provisioner.down(context, deployment)

    def remove_old_versions(self, context):
        provisioner = get_mount_provisioner(context)

        return provisioner.remove_old_versions(context, self)

    @staticmethod
    def _get_id(context, path):
        return hashlib.sha256(path.encode()).hexdigest()[:32]

    @staticmethod
    def _get_version(context, path):
        return dirhash(util.get_real_path(context, path), 'sha256')

    @staticmethod
    def from_path(context, path):
        mountId = Mount._get_id(context, path)
        mountVersion = Mount._get_version(context, path)
        deployment = context['values']['deployment_fullname']
        
        provisioner = get_mount_provisioner(context)
        mountPath = provisioner.get_mount_path(context, mountId, mountVersion, deployment)

        mount = Mount(mountId, mountVersion, path, mountPath, deployment)
        context['mounts'].append(mount)

        return mount

def apply_mounts(context):
    for mount in context['mounts']:
        names = mount.apply(context)
        for name in names:
            print('mount {} created'.format(name))

def after_apply_mounts(context):
    if context['options'].get('remove_old_mount_versions_on_apply', False):
        for mount in context['mounts']:
            removed = mount.remove_old_versions(context)
            for name in removed:
                print('mount {} removed'.format(name)) 

def down_mounts(context):
    removed = Mount.down(context)
    for name in removed:
        print('mount {} removed'.format(name))

def get_mount_provisioner(context):
    match context['options'].get('mount_provisioner', 'LocalMountProvisioner'):
        case 'SshMountProvisioner':
            return SshMountProvisioner()
        case 'LocalMountProvisioner':
            return LocalMountProvisioner()
        case _:
            return LocalMountProvisioner()

class LocalMountProvisioner:
    def get_mount_path(self, context, mountId, version, deployment):

        return os.path.join(self._get_versionless_path(context, mountId, deployment), version)
        
    def _get_idless_path(self, context, deployment): 
        basePath = context['options'].get('local_mount_provisioner_base_path', './tmp/mounts')

        return os.path.join(basePath, deployment)

    def _get_versionless_path(self, context, mountId, deployment):
        return os.path.join(self._get_idless_path(context, deployment), mountId)

    def apply(self, context, mount):
        if os.path.exists(mount.mountPath):
            return []

        return [self.create(context, mount)]

    def create(self, context, mount):
        shutil.copytree(util.get_real_path(context, mount.path), mount.mountPath)

        return mount.mountPath

    def remove_old_versions(self, context, mount):
        versionlessPath = self._get_versionless_path(context, mount.mountId, mount.deployment)

        removed = []

        for entry in os.listdir(versionlessPath):
            if entry != mount.version:
                path = os.path.join(versionlessPath, entry)
                shutil.rmtree(path)
                removed.append(path)

        return removed

    def down(self, context, deployment):
        idlessPath = self._get_idless_path(context, deployment)

        if os.path.exists(idlessPath):
            shutil.rmtree(idlessPath)
            return [idlessPath]

        return []

class SshMountProvisioner:
    def get_mount_path(self, context, mountId, version, deployment):
        return os.path.join(self._get_versionless_path(context, mountId, deployment), version)
        

    def _get_idless_path(self, context, deployment): 
        basePath = context['options']['ssh_mount_provisioner_base_path']

        return os.path.join(basePath, deployment)

    def _get_versionless_path(self, context, mountId, deployment):
        return os.path.join(self._get_idless_path(context, deployment), mountId)

    def _get_client(self, context, host):
        client = SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(AutoAddPolicy)
        client.connect(host['hostname'], port=host['port'], username=host['username'])

        return client

    def _path_exists(self, client, path):
        _, stdout, _ = client.exec_command('test -d {} && echo true'.format(path))

        return stdout.read() == b"true\n"

    def apply(self, context, mount):
        applied = []

        for host in context['options']['ssh_mount_provisioner_hosts']:
            client = self._get_client(context, host)

            if self._path_exists(client, mount.mountPath):
                continue

            applied.append(self.create(context, client, mount, host))

            client.close()

        return applied


    def create(self, context, client, mount, host):
        realPath = util.get_real_path(context, mount.path)

        client.exec_command('mkdir -p {}'.format(mount.mountPath))

        scp = SCPClient(client.get_transport())

        for entry in os.listdir(realPath):
            path = os.path.join(realPath, entry)
            scp.put(path, recursive=True, remote_path=mount.mountPath)

        scp.close()

        return '{}@{}:{}{}'.format(host['username'], host['hostname'], host['port'], mount.mountPath)

    def remove_old_versions(self, context, mount):
        versionlessPath = self._get_versionless_path(context, mount.mountId, mount.deployment)
        removed = []
        for host in context['options']['ssh_mount_provisioner_hosts']:
            client = self._get_client(context, host)

            _, stdout, _ = client.exec_command('for f in {}/*; do test "$f" != {} && rm -r $f && echo $f; done'.format(versionlessPath, mount.mountPath))

            for line in stdout.readlines():
                removed.append('{}@{}:{}{}'.format(host['username'], host['hostname'], host['port'], line.strip()))

            client.close()

        return removed

    def down(self, context, deployment):
        idlessPath = self._get_idless_path(context, deployment)
        removed = []
        for host in context['options']['ssh_mount_provisioner_hosts']:
            client = self._get_client(context, host)

            if self._path_exists(client, idlessPath):
                 _, stdout, _ = client.exec_command('rm -r {}'.format(idlessPath))
                 removed.append('{}@{}:{}{}'.format(host['username'], host['hostname'], host['port'], idlessPath))

            client.close()

        return removed