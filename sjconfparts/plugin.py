from sjconfparts.conf import *
import os

class Plugin:

    class File:
        def __init__(self, path, content, plugin_name):
            self.path = path
            self.content = content
            self.backed_up = False
            self.written = False
            self.plugin_name = plugin_name

    def __init__(self, sjconf, conf, conf_class = Conf, conf_section_class = Conf.ConfSection, conf_types = (), services_to_restart = ()):
        self.conf_class = conf_class
        self.conf_section_class = conf_section_class
        self.conf_types = conf_types
        self.services_to_restart = services_to_restart
        self.sjconf = sjconf
        self.set_conf(conf)
        self.conf_files = []
        self.files_to_backup = []

    def set_conf(self, conf):
        if self.conf_class and conf.__class__ != self.conf_class:
            self.conf = self.conf_class(conf, conf_section_class = self.conf_section_class)
        else:
            self.conf = conf
        for conf_type in self.conf_types:
            self.conf.set_type(*conf_type)

    def name(self):
        return __name__

    def get_file_content(self, file_path):
        raise NotImplemented

    def get_conf_files(self):
        return map(lambda file_path: Plugin.File(file_path, self.get_file_content(file_path), self.name()), self.conf_files)

    def get_files_to_backup(self):
        return map(lambda file_path: Plugin.File(file_path, None, self.name()), self.files_to_backup)

    def restart_all_services(self):
        for service in self.services_to_restart:
            self.restart_service(service)

    def restart_service(self, service):
        os.system('invoke-rc.d %s restart' % (service))

class PluginTemplated(Plugin):
    def get_template_path(self, file_path):
        return self.conf['template_' + os.path.basename(file_path)]

    def get_template_conf(self, file_path):
        return self.conf[self.__name__]

    def get_file_content(self, file_path):
        return open(self.get_template_path(file_path)).read() % self.get_template_conf(file_path)
