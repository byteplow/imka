import os
import os.path
import hashlib
from urllib.parse import urlparse
from git import Repo
from pathlib import Path

GIT_CHACHE_BASE_PATH = '~/.cache/imka.d4rk.io'

class FileProvider:
    basePath: str

    def __init__(self, basePath):
        self.basePath = basePath

    def isdir(self, path):
        return os.path.isdir(self.get_real_path(path))

    def exists(self, path):
        return os.path.exists(self.get_real_path(path))

    def walk(self, path):
        dir_files = []

        for root, dirs, files in os.walk(self.get_real_path(path), topdown=False):
            for name in files:
                real_path = os.path.join(root, name)
                frame_path = os.path.relpath(real_path, self.basePath)
                dir_files.append(frame_path)

        return dir_files

    def open(self, path, mode='r'):
        return open(self.get_real_path(path), mode)

    def get_real_path(self, path):
        return os.path.join(self.basePath, path)

class GitFileProvider(FileProvider):
    def __init__(self, frame_url, version):
        self.version = version
        if not self.version:
            self.version = 'main'

        url = urlparse(frame_url)
        scheme = {'git+https': 'https', 'git+ssh': 'ssh', 'git+file': 'file'}.get(url.scheme)
        self.repo_url = url._replace(scheme=scheme, fragment='').geturl()

        url_hash = hashlib.sha256(self.repo_url.encode()).hexdigest()
        self.repo_path = os.path.expanduser(os.path.join(GIT_CHACHE_BASE_PATH, url_hash[:2],url_hash))

        if not os.path.exists(self.repo_path):
            self.repo = Repo.clone_from(self.repo_url, to_path=self.repo_path)
        else:
            self.repo = Repo(self.repo_path)

        self.repo.head.reference = self.repo.commit(self.version)
        self.repo.head.reset(index=True, working_tree=True)

        self.basePath = os.path.join(self.repo_path, url.fragment)
        if not os.path.exists(self.basePath):
            raise Exception('Frame subpath ({}) in repo dose not exist - {}'.format(url.fragment, self.basePath) )
        
        self.basePath