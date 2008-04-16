class Error(Exception):
    def __str__(self):
        return self.msg

class FileError(Error):
    pass

class FileAlreadyInstalledError(FileError):
    def __init__(self, file_path):
        self.msg = "File already installed %s" % (file_path)

class FileNotInstalledError(FileError):
    def __init__(self, file_path):
        self.msg = "File not installed %s" % (file_path)

class RestoreError(Error):
    def __init__(self, exception, backup_dir):
        self.msg = "Error during restore: %s, please restore files manually from %s" % (str(exception), backup_dir)
