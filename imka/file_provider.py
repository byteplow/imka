import os
import os.path

class FileProvider():
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