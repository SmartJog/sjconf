class Error(Exception):
    def __str__(self):
        return self.msg

class FileError(Error):
    pass

class FileAlreadyInstalledError(FileError):
    def __init__(self, file_path):
        self.msg = "The file %s already installed" % (file_path)

class FileNotInstalledError(FileError):
    def __init__(self, file_path):
        self.msg = "The file %s is not installed" % (file_path)

class DistribError(Error):
    pass

class DistribAlreadyEnabledError(DistribError):
    def __init__(self, distrib_name):
        self.msg = "A distribution is already enabled: %s" % (distrib_name)

class DistribNotEnabledError(DistribError):
    def __init__(self, distrib_name):
        self.msg = "Distribution not enabled: %s" % (distrib_name)

class RestoreError(Error):
    def __init__(self, exception, backup_dir):
        self.msg = "Error during restore: %s, please restore files manually from %s" % (str(exception), backup_dir)
