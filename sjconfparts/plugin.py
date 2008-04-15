from sjconfparts.conf import *
from sjconfparts.exceptions import *
import os

class PythonIsCrappy:
    class Error(Error):
        pass

class Plugin(PythonIsCrappy):

    class MethodNotImplementedError(PythonIsCrappy.Error):
        pass

    class Dependency:
        class Error(PythonIsCrappy.Error):
            pass

        class WrongVersionError(Error):
            pass

        class NotInstalledError(Error):
            pass

        class NotEnabledError(Error):
            pass

        def __init__(self, name, optionnal = False, requirements = {}):
            self.name = name
            self.optionnal = optionnal
            for key in requirements:
                if key not in ('>=', '<=', '>>', '<<'):
                    raise TypeError
            self.requirements = requirements

        def verify(self, version):
            if '>>' in  self.requirements:
                if not version > self.requirements['>>']:
                    raise Plugin.Dependency.WrongVersionError
            if '>=' in  self.requirements:
                if not version >= self.requirements['>=']:
                    raise Plugin.Dependency.WrongVersionError
            if '<<' in  self.requirements:
                if not version < self.requirements['<<']:
                    raise Plugin.Dependency.WrongVersionError
            if '<=' in  self.requirements:
                if not version <= self.requirements['<=']:
                    raise Plugin.Dependency.WrongVersionError

    class File:
        def __init__(self, path, content, plugin_name):
            self.path = path
            self.content = content
            self.backed_up = False
            self.written = False
            self.plugin_name = plugin_name

    def __init__(self, sjconf, conf):
        self.sjconf = sjconf
        self.set_conf(conf)

    def version(self):
        raise Plugin.MethodNotImplementedError

    def dependencies(self):
        return ()

    def conf_types(self):
        return ()

    def services_to_restart(self):
        return ()

    def conf_files_path(self):
        return ()

    def files_to_backup_path(self):
        return ()

    def conf_class(self):
        return Conf

    def conf_section_class(self):
        return Conf.ConfSection

    def set_conf(self, conf):
        if (self.conf_class() and conf.__class__ != self.conf_class()) or (self.conf_section_class() and self.conf_section_class() != conf.conf_section_class):
            self.conf = self.conf_class()(conf, conf_section_class = self.conf_section_class())
        else:
            self.conf = conf
        for conf_type in self.conf_types():
            self.conf.set_type(*conf_type)

    def name(self):
        raise Plugin.MethodNotImplementedError

    def file_content(self, file_path):
        raise Plugin.MethodNotImplementedError

    def conf_files(self):
        return map(lambda file_path: Plugin.File(file_path, self.file_content(file_path), self.name()), self.conf_files_path())

    def files_to_backup(self):
        return map(lambda file_path: Plugin.File(file_path, None, self.name()), self.files_to_backup_path())

    def restart_all_services(self):
        for service in self.services_to_restart():
            self.restart_service(service)

    def restart_service(self, service):
        os.system('invoke-rc.d %s restart' % (service))

class PluginWithTemplate(Plugin):
    def template_path(self, file_path):
        section = self.name()
        if section in self.conf:
            key = 'template_' + os.path.basename(file_path)
            if not key in self.conf[section]:
                key = 'template_' + os.path.basename(file_path).replace('.conf', '')
            if not key in self.conf[section]:
                key = 'template'
        if section in self.conf and key in self.conf[section]:
            return self.sjconf.base_dir + '/' + self.conf[section][key]
        else:
            raise Plugin.MethodNotImplementedError

    def template_conf(self, file_path):
        return self.conf[self.name()]

    def file_content(self, file_path):
        return open(self.template_path(file_path)).read() % self.template_conf(file_path)
