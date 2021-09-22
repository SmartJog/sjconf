# -*- coding: utf-8 -*-
import re, os, errno, time, shutil, tarfile, glob
import imp
import sys

from sjconfparts.type import *
from sjconfparts.plugin import *
from sjconfparts.conf import *
from sjconfparts.exceptions import *
from functools import reduce


class SJConf:

    DEFAULT_SJCONF_FILE_NAME = "/etc/sjconf/sjconf.conf"

    def __init__(
        self, sjconf_file_path=DEFAULT_SJCONF_FILE_NAME, verbose=False, logger=None
    ):

        self.confs_internal = {"sjconf": Conf(file_path=sjconf_file_path)}
        self.confs_internal["sjconf"].set_type("conf", "plugins", "list")

        self.backup_dir = os.path.realpath(
            self.confs_internal["sjconf"]["conf"]["backup_dir"]
            + "/"
            + time.strftime("%F-%R:%S", time.localtime())
        )
        self.etc_dir = os.path.realpath(
            self.confs_internal["sjconf"]["conf"]["etc_dir"]
        )
        self.base_dir = os.path.realpath(
            self.confs_internal["sjconf"]["conf"]["base_dir"]
        )

        self.confs = None
        self.plugins_list = None

        self.temp_file_path = "/tmp/sjconf_tempfile.conf"

        self.files_path = {
            "plugin": os.path.realpath(
                self.confs_internal["sjconf"]["conf"]["plugins_path"]
            ),
            "template": os.path.realpath(
                self.confs_internal["sjconf"]["conf"]["templates_path"]
            ),
            "conf": self.base_dir + "/base",
            "profile": self.base_dir + "/profiles",
        }
        self.files_extensions = {
            "plugin": (".py",),
            "template": (".conf",),
            "conf": (".conf",),
            "profile": (".conf",),
        }

        self.verbose = verbose
        self.logger = logger

    def conf(self, typed=False):
        self._load_confs()
        conf = self.conf_base()
        self._load_conf_local()
        conf.update(self.confs["local"])
        if typed:
            conf = self.conf_typed(conf)
        return conf

    def conf_typed(self, conf=None):
        self._plugins_load()
        if conf is None:
            conf = self.conf()
        # We want a normal dictionary
        conf = dict(conf)
        for section_name, section in conf.items():
            conf[section_name] = dict(section)
        for plugin in self.plugins_list:
            plugin.set_conf(self.plugin_conf(plugin.name(), conf))
            for (section_name, section) in plugin.conf.items():

                def section_getitem(*args, **kw):
                    return Conf.ConfSection.__getitem__(section, *args, **kw)

                section.__getitem__ = section_getitem  # Bypass plugin's getitem method because we don't want the plugin to convert the key to its configuration file syntax

                for key in section:
                    type = section.get_type(key)
                    if type:
                        key_converted = Type.convert_key(key, type)
                        del conf[section_name][key]
                        Type.convert_safe(
                            "str", type, section, conf[section_name], key_converted
                        )
        return conf

    def conf_local(self, typed=False):
        self._load_conf_local()
        conf = Conf(self.confs["local"])
        if typed:
            conf = self.conf_typed(conf)
        return conf

    def conf_base(self, typed=False):
        self._load_conf_base()
        conf = Conf(self.confs["base"])
        self._load_conf_profile()
        if "profile" in self.confs:
            conf.update(self.confs["profile"])
        if typed:
            conf = self.conf_typed(conf)
        return conf

    def plugin_conf(self, plugin_name, conf=None):
        if conf is None:
            conf = self.conf()
        plugin_conf = Conf()
        for section in conf:
            if re.compile("^" + plugin_name + "(|:.*)$").match(section):
                plugin_conf[section] = conf[section]
        return plugin_conf

    def plugins(self):
        self._plugins_load()
        plugins = {}
        for plugin in self.plugins_list:
            plugins[plugin.name()] = plugin
        return plugins

    @classmethod
    def restart_all_services(cls, plugin):
        for service in plugin.services_to_restart():
            cls.restart_service(service)

    @classmethod
    def reload_all_services(cls, plugin):
        for service in plugin.services_to_reload():
            cls.reload_service(service)

    @classmethod
    def restart_service(cls, service):
        os.system("systemctl restart %s" % service)

    @classmethod
    def reload_service(cls, service):
        os.system("systemctl reload %s" % service)

    def restart_services(self, services_to_restart, reload=False):
        self._plugins_load()
        plugins_hash = dict([(plugin.name(), plugin) for plugin in self.plugins_list])
        if "all" in services_to_restart:
            services_to_restart.remove("all")
            for plugin_name in list(plugins_hash.keys()):
                if not plugin_name in services_to_restart:
                    services_to_restart.append(plugin_name)

        invalid_plugins = [
            plugin for plugin in services_to_restart if plugin not in plugins_hash
        ]
        if invalid_plugins:
            raise PluginsNotExistError(*invalid_plugins)
        # services_to_restart are plugins name actually
        services = set()
        for plugin in services_to_restart:
            if reload:
                services |= set(plugins_hash[plugin].services_to_reload())
            else:
                services |= set(plugins_hash[plugin].services_to_restart())
        for service in services:
            if reload:
                self.reload_service(service)
            else:
                self.restart_service(service)

    def delete_section(self, section):
        self._load_conf_local()
        conf = self.confs["local"]
        if section in conf:
            del conf[section]
        self._logger("delete section : %s" % (section))

    def delete_key(self, section, key):
        self._load_conf_local()
        conf = self.confs["local"]
        if section in conf and key in conf[section]:
            del conf[section][key]
            # If section becomes empty, remove it
            if not conf[section]:
                del conf[section]
        self._logger("delete key     : %s: %s" % (section, key))

    def set(self, section, key, value):
        self._load_conf_local()
        conf = self.confs["local"]
        conf.setdefault(section, conf.conf_section_class({}))
        conf[section][key] = value
        self._logger("set            : %s: %s = %s" % (section, key, value))

    def list_add(self, section, key, value):
        self._load_conf_local()
        conf = self.confs["local"]
        self._generic_list_add(section, key, "list", value)
        self._logger(
            "set            : %s: %s = %s" % (section, key, conf[section][key])
        )

    def list_remove(self, section, key, value):
        self._load_conf_local()
        conf = self.confs["local"]
        self._generic_list_remove(section, key, "list", value)
        self._logger(
            "set            : %s: %s = %s" % (section, key, conf[section][key])
        )

    def sequence_add(self, section, key, value):
        self._load_conf_local()
        conf = self.confs["local"]
        regexp = Type.Sequence.key_for_search(key)
        old_keys = (
            section in conf
            and dict(
                [
                    (key_to_test, value_to_test)
                    for (key_to_test, value_to_test) in conf[section].items()
                    if regexp.match(key_to_test)
                ]
            )
            or {}
        )
        self._generic_list_add(section, key, "sequence", value)
        new_keys = dict(
            [
                (key_to_test, value_to_test)
                for (key_to_test, value_to_test) in conf[section].items()
                if regexp.match(key_to_test)
            ]
        )
        conf_base = self.conf_base()
        if section in conf_base and key in conf_base[section] and key not in new_keys:
            new_keys[key] = ""
        for new_key in list(
            new_keys.keys()
        ):  # Do not use iterkeys since we are changing the dictionnary
            if (
                section in conf_base
                and new_key in conf_base[section]
                and conf_base[section][new_key] == new_keys[new_key]
            ):
                del conf[section][new_key]
                del new_keys[new_key]
        self._sequence_diff(section, key, old_keys, new_keys)

    def sequence_remove(self, section, key, value):
        self._load_conf_local()
        conf = self.confs["local"]
        regexp = re.compile("^%s-\d+$" % (key))
        old_keys = (
            section in conf
            and dict(
                [
                    (key_to_test, value_to_test)
                    for (key_to_test, value_to_test) in conf[section].items()
                    if regexp.match(key_to_test)
                ]
            )
            or {}
        )
        self._generic_list_remove(section, key, "sequence", value)
        new_keys = dict(
            [
                (key_to_test, value_to_test)
                for (key_to_test, value_to_test) in conf[section].items()
                if regexp.match(key_to_test)
            ]
        )
        self._sequence_diff(section, key, old_keys, new_keys)
        # If section becomes empty, remove it
        if not conf[section]:
            del conf[section]

    def apply_conf_modifications(self, temp=False, **kw):
        self._load_conf_local()
        conf = self.confs["local"]
        for (key, value,) in list(
            kw.items()
        ):  # We use “items” since we are modifying the dictionary
            if len(value) == 0:
                del kw[key]
        if len(kw) > 0:
            self._logger("########## Scheduled modifications ##############")

            for (key, values) in kw.items():
                for value in values:
                    getattr(self, re.sub("s$", "", key))(*value)

            self._logger("#################################################\n")

        if temp:
            output_file = self.temp_file_path
        else:
            output_file = conf.file_path
        conf.save(output_file)

    def deploy_conf(self, services_to_restart=(), services_to_reload=(), backup=True):
        self._plugins_load()
        conf_files = self._conf_files(self.plugins_list)
        if backup:
            files_to_backup = self._files_to_backup(self.plugins_list) + conf_files
            self.backup_files(files_to_backup)

        try:
            # Write all configuration files
            self._apply_confs(conf_files)

            # restart services if asked
            if len(services_to_restart) > 0:
                self.restart_services(services_to_restart)
            # reload services if asked
            if len(services_to_reload) > 0:
                self.restart_services(services_to_reload, reload=True)

            self._logger("")
        except:
            if backup:
                # Something when wrong, restoring backup files
                self.restore_files(files_to_backup)
            if len(services_to_restart) > 0:
                self.restart_services(services_to_restart)
            if len(services_to_reload) > 0:
                self.restart_services(services_to_reload, reload=True)
            # And delete backup folder
            if backup:
                self._delete_backup_dir()
            raise
        if backup:
            # Only archive once everything is OK
            self._archive_backup()
            self._logger("")
            # Delete backup, everything is cool
            self._delete_backup_dir()
        else:
            self._logger("No backup created as requested")

    def file_install(self, file_type, file_to_install, link=False):
        if self.verbose:
            self._logger("Installing file: %s" % (file_to_install))
        if os.path.exists(
            self.files_path[file_type] + "/" + os.path.basename(file_to_install)
        ):
            raise FileAlreadyInstalledError(file_to_install)
        if hasattr(self, "_file_verify_" + file_type):
            getattr(self, "_file_verify_" + file_type)(file_to_install)
        file_destination_path = (
            self.files_path[file_type] + "/" + os.path.basename(file_to_install)
        )
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
        self._file_uninstall_cleanup(file_type, file_to_uninstall)
        file_to_uninstall_path = self._file_path(file_type, file_to_uninstall)
        if not os.path.islink(file_to_uninstall_path) and os.path.isdir(
            file_to_uninstall_path
        ):
            shutil.rmtree(file_to_uninstall_path)
        else:
            os.unlink(file_to_uninstall_path)
        if self.verbose:
            self._logger("Uninstalled file: %s" % (file_to_uninstall))

    def plugin_enable(self, plugin_to_enable):
        # ensure the plugin in installed
        self._file_path("plugin", plugin_to_enable)
        plugins_list = self.confs_internal["sjconf"]["conf"]["plugins_list"]
        if plugin_to_enable in plugins_list:
            raise Plugin.AlreadyEnabledError(plugin_to_enable)
        self.confs_internal["sjconf"]["conf"]["plugins_list"].append(plugin_to_enable)
        self.confs_internal["sjconf"].save()

    def plugin_disable(self, plugin_to_disable):
        try:
            self.confs_internal["sjconf"]["conf"]["plugins_list"].remove(
                plugin_to_disable
            )
        except ValueError:
            raise Plugin.NotEnabledError(plugin_to_disable)
        self.confs_internal["sjconf"].save()

    def profile_enable(self, profile_to_enable, level=1):
        # ensure the profile in installed
        self._load_conf_local()
        self._file_path("profile", profile_to_enable)
        enabled_level = self._profile_level(profile_to_enable)
        if enabled_level != None:
            raise ProfileAlreadyEnabledError(profile_to_enable, enabled_level)
        key = "profiles-" + str(level)
        self.confs["local"].setdefault("sjconf", Conf.ConfSection())
        self.confs["local"]["sjconf"].setdefault(key, "")
        Type.convert("str", "list", self.confs["local"]["sjconf"], {}, key)[key].append(
            profile_to_enable
        )
        self.confs["local"].save()

    def profile_disable(self, profile_to_disable):
        self._load_conf_local()
        # ensure the profile in installed
        self._file_path("profile", profile_to_disable)
        level = self._profile_level(profile_to_disable)
        if level == None:
            raise ProfileNotEnabledError(profile_to_disable)
        key = "profiles-" + str(level)
        Type.convert("str", "list", self.confs["local"]["sjconf"], {}, key)[key].remove(
            profile_to_disable
        )
        if self.confs["local"]["sjconf"][key] == "":
            del self.confs["local"]["sjconf"][key]
        self.confs["local"].save()

    def plugins_infos(self, plugins_to_list=None):
        if plugins_to_list == None:
            plugins_to_list = list(
                map(
                    lambda plugin_path: os.path.basename(plugin_path).replace(
                        ".py", ""
                    ),
                    glob.glob(
                        self.confs_internal["sjconf"]["conf"]["plugins_path"] + "/*.py"
                    ),
                )
            )
        plugins = self._plugins_init(plugins_to_list)
        plugins_hash = {}
        for plugin in plugins:
            plugins_hash[plugin.name()] = plugin
        plugins_list = {}
        for plugin in plugins:
            plugins_list[plugin.name()] = self._plugin_list(plugin, plugins_hash)
        return plugins_list

    def profiles_infos(self, profiles_to_list=None):
        if profiles_to_list == None:
            profiles_to_list = list(
                map(
                    lambda profile_path: os.path.basename(profile_path).replace(
                        ".conf", ""
                    ),
                    glob.glob(self.files_path["profile"] + "/*.conf"),
                )
            )
        profiles_hash = {}
        for profile in profiles_to_list:
            level = self._profile_level(profile)
            profiles_hash[profile] = level
        return profiles_hash

    def backup_files(self, files_to_backup=None):
        self._load_conf_local()
        if files_to_backup == None:
            self._plugins_load()
            files_to_backup = self._files_to_backup(
                self.plugins_list
            ) + self._conf_files(self.plugins_list)
        self._logger("Backup folder : %s" % self.backup_dir)
        os.makedirs(self.backup_dir)
        os.makedirs(self.backup_dir + "/sjconf/")
        shutil.copy(self.confs["local"].file_path, self.backup_dir + "/sjconf")
        # Store all files into a service dedicated folder
        for file_to_backup in files_to_backup:
            if not os.path.isfile(file_to_backup.path):
                continue
            if not os.path.isdir(self.backup_dir + "/" + file_to_backup.plugin_name):
                os.makedirs(self.backup_dir + "/" + file_to_backup.plugin_name)
            file_to_backup.backup_path = (
                self.backup_dir
                + "/"
                + file_to_backup.plugin_name
                + "/"
                + os.path.basename(file_to_backup.path)
            )
            shutil.move(file_to_backup.path, file_to_backup.backup_path)
            file_to_backup.backed_up = True
        return files_to_backup

    def _logger(self, str):
        if self.logger:
            self.logger(str)

    def _plugin_list(self, plugin_to_list, plugins_hash):
        plugin_info = {}
        plugin_info["plugin"] = plugin_to_list
        plugin_info["is_enabled"] = (
            plugin_to_list.name()
            in self.confs_internal["sjconf"]["conf"]["plugins_list"]
        )
        plugin_info["dependencies"] = {}
        for dependency in plugin_to_list.dependencies():
            plugin_info["dependencies"][dependency.name] = {}
            plugin_info["dependencies"][dependency.name]["dependency"] = dependency
            plugin_info["dependencies"][dependency.name]["is_enabled"] = (
                dependency.name in self.confs_internal["sjconf"]["conf"]["plugins_list"]
            )
            plugin_info["dependencies"][dependency.name]["plugin"] = (
                dependency.name in plugins_hash and plugins_hash[dependency.name]
            ) or None
            try:
                self._plugin_dependency_verify(plugin_to_list, dependency, plugins_hash)
                plugin_info["dependencies"][dependency.name]["state"] = True
            except Plugin.Dependency.Error as exception:
                plugin_info["dependencies"][dependency.name]["state"] = exception
        return plugin_info

    def _plugin_dependency_verify(self, plugin, dependency, plugins_hash):
        if (
            not dependency.name in self.confs_internal["sjconf"]["conf"]["plugins_list"]
            and not dependency.optional
        ):  # Plugin is not available, find out if it is not installed or not enabled
            try:
                self._file_path(
                    "plugin", dependency.name
                )  # This will raise an Error if plugin is not installed
                raise Plugin.Dependency.NotEnabledError(plugin.name(), dependency.name)
            except FileNotInstalledError:
                raise Plugin.Dependency.NotInstalledError(
                    plugin.name(), dependency.name
                )

        if (
            dependency.name in self.confs_internal["sjconf"]["conf"]["plugins_list"]
            and dependency.name in plugins_hash
        ):
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

    def _plugins_init(self, plugins_list=None):
        if plugins_list == None:
            plugins_list = self.confs_internal["sjconf"]["conf"]["plugins_list"]

        # FIXME: Most of the code below can and should be reused for all other
        # projects that load python plugins.

        # fake 'sjconf.plugins' package in which we will shove our plugins
        if "sjconf.plugins" not in sys.modules:
            sys.modules["sjconf.plugins"] = imp.new_module("sjconf.plugins")

        plugins = []
        for plugin in plugins_list:
            # Using this method of import, we do not have to modify
            # sys.path, which could pose problems for people using us
            # in an other Python program
            plugin_module = imp.load_module(
                "sjconf.plugins." + plugin,
                *imp.find_module(plugin, [self.files_path["plugin"]])
            )

            plugins.append(plugin_module.Plugin(plugin, self, self.plugin_conf(plugin)))
        return plugins

    def _plugins_load(self):
        if self.plugins_list == None:
            self.plugins_list = self._plugins_init()
            self._plugins_dependencies(self.plugins_list)

    def _files_to_backup(self, plugins):
        return reduce(
            lambda files_to_backup, plugin: files_to_backup + plugin.files_to_backup(),
            plugins,
            [],
        )

    def _archive_backup(self):
        # Once configuration is saved, we can archive backup into a tgz
        path = "%s/sjconf_backup_%s.tgz" % (
            os.path.dirname(self.backup_dir),
            os.path.basename(self.backup_dir),
        )
        self._logger("Backup file : %s" % path)
        with tarfile.open(path, "w:gz") as tar:
            tar.add(self.backup_dir)

    def _delete_backup_dir(self, dir=None):
        # Once backup has been archived, delete it
        if dir == None:
            dir = self.backup_dir
            self._logger("Deleting folder %s" % dir)

        for entry in os.listdir(dir):
            path = dir + "/" + entry
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
                except shutil.Error as exception:
                    raise RestoreError(exception, self.backup_dir)

    def _load_confs(self, force=False):
        self._load_conf_local(force)
        self._load_conf_profile(force)
        self._load_conf_base(force)

    def _load_conf_local(self, force=False):
        if not self.confs:
            self.confs = {}
        if not "local" in self.confs or force:
            self.confs["local"] = self._load_conf_part("local", "raw")
            self.confs["local"].set_type("sjconf", "profiles", "sequence")

    def _load_conf_profile(self, force=False):
        if not self.confs:
            self.confs = {}
        self._load_conf_local(force)
        if (not "profile" in self.confs or force) and "sjconf" in self.confs["local"]:
            self.confs["profile"] = self._load_conf(
                [
                    [
                        ("profiles/" + profile, "magic")
                        for profile in Type.convert(
                            "str", "list", {"profiles": profiles}, {}, "profiles"
                        )["profiles"]
                    ]
                    for profiles in self.confs["local"]["sjconf"]["profiles_sequence"]
                ],
                self.confs["local"],
            )

    def _load_conf_base(self, force=False):
        if not self.confs:
            self.confs = {}
        if not "base" in self.confs or force:
            self.confs["base"] = self._load_conf_part("base", "magic")

    def _load_conf(self, conf_files, conf_local):
        conf = Conf()
        conf_level_parts = []
        conf_files.reverse()
        for conf_level_files in conf_files:
            conf_level_parts.append(
                self._load_conf_level(conf_level_files, conf_level_parts + [conf_local])
            )
        conf_level_parts.reverse()
        for conf_level_part in conf_level_parts:
            conf.update(conf_level_part)
        if len(conf_level_parts) == 1:
            conf.file_path = conf_level_parts[0].file_path
        conf_files.reverse()
        return conf

    def _load_conf_level(self, conf_level_files, conf_level_parts):
        conf_level = Conf()
        conf_parts = []
        for (conf_file, conf_type) in conf_level_files:
            conf_part = self._load_conf_part(conf_file, conf_type)
            self._verify_conflict(conf_part, conf_parts, conf_level_parts)
            conf_parts.append(conf_part)
        for conf_part in conf_parts:
            conf_level.update(conf_part)
        if len(conf_parts) == 1:
            conf_level.file_path = conf_parts[0].file_path
        return conf_level

    def _load_conf_part(self, conf_file, conf_type):
        conf_file_path = os.path.realpath(self.base_dir + "/" + conf_file)
        if not os.path.exists(conf_file_path):
            conf_file_path += ".conf"
        return Conf(file_path=conf_file_path, parser_type=conf_type)

    def _overriden_in_level(self, conf_level_parts, section, key):
        for other_conf_level_part in conf_level_parts:
            if (
                section in other_conf_level_part
                and key in other_conf_level_part[section]
            ):
                return True
        return False

    def _verify_conflict(self, conf_part, conf_parts, conf_level_parts):
        for other_conf_part in conf_parts:
            conflicting_values = conf_part.update_verify_conflict(other_conf_part)
            if len(conflicting_values) != 0:
                for conflicting_value in conflicting_values:
                    section = conflicting_value[0]
                    key = conflicting_value[1]
                    if not self._overriden_in_level(conf_level_parts, section, key):
                        conf_part_name = os.path.basename(conf_part.file_path).replace(
                            ".conf", ""
                        )
                        other_conf_part_name = os.path.basename(
                            other_conf_part.file_path
                        ).replace(".conf", "")
                        raise Conf.ProfileConflictError(
                            conf_part_name, other_conf_part_name, section, key
                        )

    def _profile_level(self, profile):
        self._load_conf_local()
        regexp = re.compile("^profiles-(\d+)$")
        if not "sjconf" in self.confs["local"]:
            return None
        for key in self.confs["local"]["sjconf"]:
            match_results = regexp.match(key)
            if (
                match_results
                and profile
                in Type.convert("str", "list", self.confs["local"]["sjconf"], {}, key)[
                    key
                ]
            ):
                return int(match_results.group(1))
        return None

    def _apply_confs(self, conf_files=None):
        # Open and write all configuration files
        if conf_files == None:
            self._plugins_load()
            conf_files = self._conf_files(self.plugins_list)
        for conf_file in conf_files:
            self._logger(
                "Writing configuration file %s (%s)"
                % (conf_file.path, conf_file.plugin_name)
            )
            # checking if the dirname exists
            folder = os.path.dirname(conf_file.path)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with open(conf_file.path + ".sjconf", "w") as fi:
                fi.write(conf_file.content)
            os.rename(conf_file.path + ".sjconf", conf_file.path)
            conf_file.written = True
        self._logger("")

    def _conf_files(self, plugins):
        return reduce(
            lambda conf_files, plugin: conf_files + plugin.conf_files(), plugins, []
        )

    def _file_verify_conf(self, conf_file_to_verify):
        conf_file_to_verify_name = os.path.basename(conf_file_to_verify).replace(
            ".conf", ""
        )
        conf_to_verify = Conf(file_path=conf_file_to_verify)
        for section in conf_to_verify:
            if not re.compile(conf_file_to_verify_name + ":?.*").match(section):
                raise Conf.UnauthorizedSectionError(section, conf_file_to_verify_name)

    def _file_path(self, file_type, file_path):
        file_path = file_path
        if not file_path.startswith(self.files_path[file_type]):
            file_path = self.files_path[file_type] + "/" + file_path
        tmp_file_path = file_path
        for extension in self.files_extensions[file_type]:
            if os.path.exists(file_path):
                break
            file_path = tmp_file_path + extension
        if not os.path.exists(file_path):
            raise FileNotInstalledError(file_path)
        return file_path

    def _file_uninstall_cleanup(self, type, file):
        """
        function        _file_uninstall_cleanup
        description     remove references about a file in the configuration
                        (e.g. disable file usage) in order to get a proper
                        state before uninstall this file
        arguments       type - type of file to delete
                        file - name of file to delete
        return          none
        """

        if (
            type == "profile" and self.profiles_infos([file])[file] != None
        ):  # Profile file currenly used
            self.profile_disable(file)
        elif (
            type == "plugin" and self.plugins_infos([file])[file]["is_enabled"]
        ):  # Plugin file currently used
            self.plugin_disable(file)

    def _generic_list_add(self, section, key, type, value):
        key_typed = key + "_" + type
        try:
            conf = self.conf_local()
            conf.set_type(section, key, type)
            value_old = conf[section][key_typed]
        except KeyError:
            try:
                conf = self.conf_base()
                conf.set_type(section, key, type)
                value_old = conf[section][key_typed]
                self._logger(
                    'The key "%s" in section "%s" does not exist in local configuration, but exist in base or profile configuration, the new value will be appended to "%s".'
                    % (key, section, repr(value_old))
                )
            except KeyError:
                value_old = []
        if value in value_old:
            raise Conf.ListValueAlreadyExistError(section, key, value)
        self._generic_list_modify(section, key, type, value, "append")

    def _generic_list_remove(self, section, key, type, value):
        key_typed = key + "_" + type
        try:
            conf = self.conf_local()
            conf.set_type(section, key, type)
            conf[section][key_typed]
        except KeyError:
            conf = self.conf_base()
            conf.set_type(section, key, type)
            value_base = conf[section][key_typed]
            self._logger(
                'The key "%s" in section "%s" does not exist in local configuration, but exist in base or profile configuration, the new value will be removed from "%s".'
                % (key, section, repr(value_base))
            )
        self._generic_list_modify(section, key, type, value, "remove")

    def _generic_list_modify(self, section, key, type, value, method):
        conf = self.conf()
        key_typed = key + "_" + type
        if section not in conf:
            conf[section] = conf.conf_section_class()
        conf.set_type(section, key, type)
        try:
            conf[section][key_typed]
        except KeyError:
            conf[section][key_typed] = []
        old_keys = dict(conf[section])
        getattr(conf[section][key_typed], method)(value)
        if section not in self.confs["local"]:
            self.confs["local"][section] = conf.conf_section_class()
        for new_key, new_value in conf[section].items():
            if new_value != old_keys.get(new_key):
                self.confs["local"][section][new_key] = new_value
        conf_base = self.conf_base().get(section)
        for old_key in old_keys:
            if old_key not in conf[section]:
                if conf_base and old_key in conf_base:
                    self.confs["local"][section][old_key] = ""
                else:
                    del self.confs["local"][section][old_key]

    def _sequence_diff(self, section, key, old_keys, new_keys):
        for key in old_keys:
            if not key in new_keys:
                self._logger("delete key     : %s: %s" % (section, key))
        for (key, value) in new_keys.items():
            if not key in old_keys or value != old_keys[key]:
                self._logger("set            : %s: %s = %s" % (section, key, value))
