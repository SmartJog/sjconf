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
    def __init__(self, distrib, level):
        self.msg = "The distribution %s is already enabled at level %s" % (distrib, level)

class DistribNotEnabledError(DistribError):
    def __init__(self, distrib):
        self.msg = "The distribution %s is not enabled" % (distrib)

class RestoreError(Error):
    def __init__(self, exception, backup_dir):
        self.msg = "Error during restore: %s, please restore files manually from %s" % (str(exception), backup_dir)

class ProfileAlreadyEnabledError(Error):
    def __init__(self, profile_name, profile_level):
    	self.msg = "Profile already enabled: %s, level: %s" % (profile_name, profile_level)

class ProfileNotEnabledError(Error):
    def __init__(self, profile_name):
    	self.msg = "Profile not enabled: %s" % (profile_name)

class PluginsNotExistError(Error):
    def __init__(self, *plugins):
        self.msg = 'Plugin%s ' % (len(plugins) > 1 and 's' or '') + ', '.join(plugins) + ' do%s ' % (len(plugins) == 1 and 'es' or '') + "not exist"
