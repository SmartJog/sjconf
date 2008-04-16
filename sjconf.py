import re, sys, os, errno, time, shutil, tarfile, glob

from sjconfparts.type import *
from sjconfparts.plugin import *
from sjconfparts.conf import *
from sjconfparts.exceptions import *

class SJConf:

    DEFAULT_SJCONF_FILE_NAME = '/etc/smartjog/sjconf.conf'

    def __init__(self, sjconf_file_path = DEFAULT_SJCONF_FILE_NAME, verbose = False, logger = None):

        self.confs_internal = {'sjconf' : Conf(file_path = sjconf_file_path)}
        self.confs_internal['sjconf'].set_type('conf', 'plugins', 'list')

        self.backup_dir = os.path.realpath(self.confs_internal['sjconf']['conf']['backup_dir'] + '/' + time.strftime('%F-%R:%S', time.localtime()))
        self.etc_dir = os.path.realpath(self.confs_internal['sjconf']['conf']['etc_dir'])
        self.base_dir = os.path.realpath(self.confs_internal['sjconf']['conf']['base_dir'])

        conf_files = {}
        conf_files['base'] = 'base'
        distrib = self.confs_internal['sjconf']['conf']['distrib']
        if distrib != '':
            conf_files['distrib'] = distrib
        conf_files['local'] = 'local'

        self.confs = {}
        for conf in conf_files:
            conf_file_path = os.path.realpath(self.base_dir + '/' + conf_files[conf])
            if not os.path.exists(conf_file_path):
                conf_file_path += '.conf'
            self.confs[conf] = Conf(file_path = conf_file_path)

        self.temp_file_path = "/tmp/sjconf_tempfile.conf"

        self.files_path = {
            'plugin' : os.path.realpath(self.confs_internal['sjconf']['conf']['plugins_path']),
            'template' : os.path.realpath(self.confs_internal['sjconf']['conf']['templates_path']),
            'conf' : self.base_dir + '/base'
        }
        self.files_extensions = {'plugin' : ('.py',), 'template' : ('.conf',), 'conf' : ('.conf',)}

        sys.path.append(self.files_path['plugin'])

        self.verbose = verbose
        self.logger = logger

    def conf(self):
        conf = Conf(self.confs['base'])
        if 'distrib' in self.confs:
            conf.update(self.confs['distrib'])
        conf.update(self.confs['local'])
        return conf

    def plugin_conf(self, plugin_name):
        conf = self.conf()
        plugin_conf = Conf()
        for section in conf:
            if re.compile(plugin_name + ':?.*').match(section):
                plugin_conf[section] = conf[section]
        return plugin_conf

    def restart_services(self, services_to_restart, plugins = None):
        if plugins == None:
            plugins = self._plugins_load()
        already_restart = []
        for plugin in plugins:
            if plugin in services_to_restart or 'all' in services_to_restart:
                plugin.restart_all_services()

    def apply_conf_modifications(self, sets = [], list_adds = [], list_deletions = [], delete_keys = [], delete_sections = [], temp = False):
        conf = self.confs['local']
        if sets or delete_keys or delete_sections or list_adds or list_deletions:
            self._logger("########## Scheduled modifications ##############")

            for section in delete_sections:
                if section in conf:
                    del(conf[section])
                self._logger('delete section : %s' % (section))

            for section, key in delete_keys:
                if section in conf:
                    if key in conf[section]:
                        del(conf[section][key])
                self._logger('delete key     : %s: %s' % (section, key))

            for section, key, value in sets:
                conf.setdefault(section, conf.conf_section_class({}))
                conf[section][key] = value
                self._logger('set            : %s: %s = %s' % (section, key, value))

            for section, key, value in list_adds:
                if section not in conf:
                    conf[section] = conf.conf_section_class()
                if key not in conf[section]:
                    confs_to_test = ['base']
                    if 'distrib' in self.confs:
                        confs_to_test.append('distrib')
                    for conf_to_test in confs_to_test:
                        if section in self.confs[conf_to_test] and key in self.confs[conf_to_test][section] and self.confs[conf_to_test][section][key] != '':
                            raise Conf.ListExistInParentError(section, key, conf_to_test)
                    conf[section][key] = ''
                conf.set_type(section, key, 'list')
                if value in conf[section][key + '_list']:
                    raise Conf.ListValueAlreadyExistError(section, key, value)
                conf[section][key + '_list'].append(value)
                self._logger('set            : %s: %s = %s' % (section, key, conf[section][key]))

            for section, key, value in list_deletions:
                conf.set_type(section, key, 'list')
                conf[section][key + '_list'].remove(value)
                self._logger('set            : %s: %s = %s' % (section, key, conf[section][key]))

            self._logger("#################################################\n")

        if temp:
            output_file = self.temp_file_path
        else:
            output_file = conf.file_path
        conf.save(output_file)

    def deploy_conf(self, services_to_restart):
        plugins = self._plugins_load()
        conf_files = self._conf_files(plugins)
        files_to_backup = self._files_to_backup(plugins) + conf_files
        self.backup_files(files_to_backup)

        try:
            # Write all configuration files
            self._apply_confs(conf_files)

            # restart services if asked
            if len(services_to_restart) > 0:
                self.restart_services(services_to_restart, plugins)
            self._logger('')
        except:
            # Something when wrong, restoring backup files
            self.restore_files(files_to_backup)
            if len(services_to_restart) > 0:
                self.restart_services(services_to_restart, plugins)
            # And delete backup folder
            self._delete_backup_dir()
            raise
        # Only archive once everything is OK
        self._archive_backup()
        self._logger('')
        # Delete backup, everything is cool
        self._delete_backup_dir()

    def file_install(self, file_type, file_to_install, link=False):
        if self.verbose:
           self. _logger("Installing file: %s" % (file_to_install))
        if os.path.exists(self.files_path[file_type] + '/' + os.path.basename(file_to_install)):
            raise FileAlreadyInstalledError(file_to_install)
        if hasattr(self, '_file_verify_' + file_type):
            getattr(self, '_file_verify_' + file_type)(file_to_install)
        file_destination_path = self.files_path[file_type] + '/' + os.path.basename(file_to_install)
        if not link:
            if os.path.isdir(file_to_install):
                shutil.copytree(file_to_install, file_destination_path)
            else:
                shutil.copy(file_to_install, file_destination_path)
        else:
            os.symlink(os.path.realpath(file_to_install), file_destination_path)
        if self.verbose:
            self._logger("Installed file: %s" % (file_to_install))

    def file_uninstall(self, file_type, file_to_uninstall):
        if self.verbose:
            self._logger("Uninstalling file: %s" % (file_to_uninstall))
        file_to_uninstall_path = self._file_path(file_type, file_to_uninstall)
        if not os.path.islink(file_to_uninstall_path) and os.path.isdir(file_to_uninstall_path):
            shutil.rmtree(file_to_uninstall_path)
        else:
            os.unlink(file_to_uninstall_path)
        if self.verbose:
            self._logger("Uninstalled file: %s" % (file_to_uninstall))

    def plugin_enable(self, plugin_to_enable):
        # ensure the plugin in installed
        self._file_path('plugin', plugin_to_enable)
        plugins_list = self.confs_internal['sjconf']['conf']['plugins_list']
        if plugin_to_enable in plugins_list:
            raise Plugin.AlreadyEnabledError(plugin_to_enable)
        self.confs_internal['sjconf']['conf']['plugins_list'].append(plugin_to_enable)
        self.confs_internal['sjconf'].save()

    def plugin_disable(self, plugin_to_disable):
        # ensure the plugin in installed
        self._file_path('plugin', plugin_to_disable)
        try:
            self.confs_internal['sjconf']['conf']['plugins_list'].remove(plugin_to_disable)
        except ValueError:
            raise Plugin.NotEnabledError(plugin_to_disable)
        self.confs_internal['sjconf'].save()

    def plugins_list(self, plugins_to_list = None):
        if plugins_to_list == None:
            plugins_to_list = map(lambda plugin_path: os.path.basename(plugin_path).replace('.py', ''), glob.glob(self.confs_internal['sjconf']['conf']['plugins_path'] + '/*.py'))
        plugins = self._plugins_init(plugins_to_list)
        plugins_hash = {}
        for plugin in plugins:
            plugins_hash[plugin.name()] = plugin
        plugins_list = {}
        for plugin in plugins:
            plugins_list[plugin.name()] = self._plugin_list(plugin, plugins_hash)
        return plugins_list

    def _logger(self, str):
        if self.logger:
            self.logger(str)

    def _plugin_list(self, plugin_to_list, plugins_hash):
        plugin_info = {}
        plugin_info['plugin'] = plugin_to_list
        plugin_info['is_enabled'] = plugin_to_list.name() in self.confs_internal['sjconf']['conf']['plugins_list']
        plugin_info['dependencies'] = {}
        for dependency in plugin_to_list.dependencies():
            plugin_info['dependencies'][dependency.name] = {}
            plugin_info['dependencies'][dependency.name]['dependency'] = dependency
            plugin_info['dependencies'][dependency.name]['is_enabled'] = dependency.name in self.confs_internal['sjconf']['conf']['plugins_list']
            plugin_info['dependencies'][dependency.name]['plugin'] = (dependency.name in plugins_hash and plugins_hash[dependency.name]) or None
            try:
                self._plugin_dependency_verify(plugin_to_list, dependency, plugins_hash)
                plugin_info['dependencies'][dependency.name]['state'] = True
            except Plugin.Dependency.Error, exception:
                plugin_info['dependencies'][dependency.name]['state'] = exception
        return plugin_info

    def _plugin_dependency_verify(self, plugin, dependency, plugins_hash):
        if not dependency.name in self.confs_internal['sjconf']['conf']['plugins_list'] and not dependency.optional: # Plugin is not available, find out if it is not installed or not enabled
            try:
                self._file_path('plugin', dependency.name) # This will raise an Error if plugin is not installed
                raise Plugin.Dependency.NotEnabledError(plugin.name(), dependency.name)
            except FileNotInstalledError:
                raise Plugin.Dependency.NotInstalledError(plugin.name(), dependency.name)
        if dependency.name in self.confs_internal['sjconf']['conf']['plugins_list']:
            dependency.verify(plugins_hash[dependency.name].version())

    def _plugin_dependencies(self, plugin, plugins_hash):
        plugin_dependencies_hash = {}
        for dependency in plugin.dependencies():
            if not dependency.name in plugins_hash and dependency.optional:
                continue
            self._plugin_dependency_verify(plugin, dependency, plugins_hash)
            plugin_dependencies_hash[dependency.name] = plugins_hash[dependency.name]
        return plugin_dependencies_hash

    def _plugins_dependencies(self, plugins):
        plugins_hash = {}
        for plugin in plugins:
            plugins_hash[plugin.name()] = plugin
        for plugin in plugins:
            plugin_dependencies_hash = self._plugin_dependencies(plugin, plugins_hash)
            if len(plugin_dependencies_hash) > 0: 
                plugin.set_plugins(plugin_dependencies_hash)

    def _plugins_init(self, plugins_list = None):
        if plugins_list == None:
            plugins_list = self.confs_internal['sjconf']['conf']['plugins_list']
        plugins = []
        for plugin in plugins_list:
            plugins.append(__import__(plugin).Plugin(plugin, self, self.plugin_conf(plugin)))
        return plugins

    def _plugins_load(self):
        plugins = self._plugins_init()
        self._plugins_dependencies(plugins)
        return plugins

    def _files_to_backup(self, plugins):
        return reduce(lambda files_to_backup, plugin: files_to_backup + plugin.files_to_backup(), plugins, [])

    def backup_files(self, files_to_backup = None, plugins = None):
        if files_to_backup == None:
            if plugins == None:
                plugins = self._plugins_load()
            files_to_backup = self._files_to_backup(plugins) + self._conf_files(plugins)
        self._logger( "Backup folder : %s" % self.backup_dir )
        os.makedirs(self.backup_dir)
        os.makedirs(self.backup_dir + '/sjconf/')
        shutil.copy(self.confs['local'].file_path, self.backup_dir + '/sjconf')
        # Store all files into a service dedicated folder
        for file_to_backup in files_to_backup:
            if not os.path.isfile(file_to_backup.path):
                continue
            if not os.path.isdir(self.backup_dir + '/' + file_to_backup.plugin_name):
                os.makedirs(self.backup_dir + '/' + file_to_backup.plugin_name)
            file_to_backup.backup_path = self.backup_dir + '/' + file_to_backup.plugin_name + '/' + os.path.basename(file_to_backup.path)
            shutil.move(file_to_backup.path, file_to_backup.backup_path)
            file_to_backup.backed_up = True
        return files_to_backup

    def _archive_backup(self):
        # Once configuration is saved, we can archive backup into a tgz
        path = "%s/sjconf_backup_%s.tgz" % (os.path.dirname(self.backup_dir), os.path.basename(self.backup_dir))
        self._logger("Backup file : %s" % path)
        tarfile.open(path, 'w:gz').add(self.backup_dir)

    def _delete_backup_dir(self, dir=None):
        # Once backup has been archived, delete it
        if dir == None:
            dir = self.backup_dir
            self._logger("Deleting folder %s" % dir)

        for entry in os.listdir(dir):
            path = dir + '/' + entry
            if os.path.isdir(path):
                self._delete_backup_dir(path)
            elif os.path.isfile(path):
                os.unlink(path)
        os.rmdir(dir)

    def restore_files(self, backed_up_files):
        # Something went wrong
        self._logger("Restoring files from %s" % self.backup_dir)

        # Unlink all conf files just created
        for backed_up_file in backed_up_files:
            if backed_up_file.written and os.path.isfile(backed_up_file.path):
                os.unlink(backed_up_file.path)

        # Restore backup files
        for backed_up_file in backed_up_files:
            if backed_up_file.backed_up:
                try:
                    shutil.move(backed_up_file.backup_path, backed_up_file.path)
                except shutil.Error, exception:
                    raise RestoreError(exception, self.backup_dir)

    def _apply_confs(self, conf_files = None, plugins = None):
        # Open and write all configuration files
        if conf_files == None:
            if plugins == None:
                plugins = self._plugins_load()
            conf_files = self._conf_files(plugins)
        for conf_file in conf_files:
            self._logger("Writing configuration file %s (%s)" % (conf_file.path, conf_file.plugin_name))
            # checking if the dirname exists
            folder = os.path.dirname(conf_file.path)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            open(conf_file.path, "w").write(conf_file.content)
            conf_file.written = True
        self._logger('')

    def _conf_files(self, plugins):
        return reduce(lambda conf_files, plugin: conf_files + plugin.conf_files(), plugins, [])

    def _file_verify_conf(self, conf_file_to_verify):
        conf_file_to_verify_name = os.path.basename(conf_file_to_verify).replace('.conf', '')
        conf_to_verify = Conf(file_path = conf_file_to_verify)
        for section in conf_to_verify:
            if not re.compile(conf_file_to_verify_name + ':?.*').match(section):
                raise Conf.UnauthorizedSectionError(section, conf_file_to_verify_name)

    def _file_path(self, file_type, file_path):
        file_path = file_path
        if not file_path.startswith(self.files_path[file_type]):
            file_path = self.files_path[file_type] + '/' + file_path
        tmp_file_path = file_path
        for extension in self.files_extensions[file_type]:
            if os.path.exists(file_path):
                break
            file_path = tmp_file_path + extension
        if not os.path.exists(file_path):
            raise FileNotInstalledError(file_path)
        return file_path
