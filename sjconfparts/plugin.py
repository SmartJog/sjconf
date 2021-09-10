import os

import apt_pkg

import sjconfparts.exceptions
from sjconfparts.conf import *


class Plugin:
    """Base class to implement SJConf plugins."""

    class Error(sjconfparts.exceptions.Error):
        pass

    class MethodNotImplementedError(Error):
        def __init__(self, plugin_name, method_name):
            self.msg = 'Method "%s" not implemented in plugin %s' % (
                method_name,
                plugin_name,
            )

    class AlreadyEnabledError(Error):
        def __init__(self, plugin_name):
            self.msg = "Plugin already enabled: %s" % (plugin_name)

    class NotEnabledError(Error):
        def __init__(self, plugin_name):
            self.msg = "Plugin not enabled: %s" % (plugin_name)

    class Dependency:
        """Dependency helper class.

        Embeds various methods to verify that plugin dependencies are valid and
        satisfied.
        """

        class Error(Error):
            pass

        class BadVersionError(Error):
            def __init__(
                self,
                plugin_name,
                dependency,
                installed_version,
                requirement,
                requirement_version,
            ):
                self.msg = "Plugin %s depends on plugin %s version %s %s, but version %s is installed" % (
                    plugin_name,
                    dependency,
                    requirement,
                    requirement_version,
                    installed_version,
                )

        class NotInstalledError(Error):
            def __init__(self, plugin_name, dependency):
                self.msg = "Plugin %s depends on plugin %s but it is not installed" % (
                    plugin_name,
                    dependency,
                )

        class NotEnabledError(Error):
            def __init__(self, plugin_name, dependency):
                self.msg = "Plugin %s depends on plugin %s but it is not enabled" % (
                    plugin_name,
                    dependency,
                )

        class BadRequirementTypeError(Error):
            def __init__(self, plugin_name, dependency, requirement):
                self.msg = (
                    'Plugin %s declares a dependency on plugin %s with an invalid requirement type "%s"'
                    % (plugin_name, dependency, requirement)
                )

        def __init__(self, plugin, name, optional=False, requirements={}):
            self.name = name
            self.plugin = plugin
            self.optional = optional
            for key in requirements:
                if key not in ("=", ">=", "<=", ">", "<"):
                    raise BadRequirementTypeError(self.plugin.name(), self.name, key)
            self.requirements = requirements

        def verify(self, version):
            apt_pkg.init_system()

            if "=" in self.requirements:
                if not apt_pkg.version_compare(version, self.requirements["="]) == 0:
                    raise Plugin.Dependency.BadVersionError(
                        self.plugin.name(),
                        self.name,
                        version,
                        "=",
                        self.requirements["="],
                    )
            if ">" in self.requirements:
                if not apt_pkg.version_compare(version, self.requirements[">"]) > 0:
                    raise Plugin.Dependency.BadVersionError(
                        self.plugin.name(),
                        self.name,
                        version,
                        ">",
                        self.requirements[">"],
                    )
            if ">=" in self.requirements:
                if not apt_pkg.version_compare(version, self.requirements[">="]) >= 0:
                    raise Plugin.Dependency.BadVersionError(
                        self.plugin.name(),
                        self.name,
                        version,
                        ">=",
                        self.requirements[">="],
                    )
            if "<" in self.requirements:
                if not apt_pkg.version_compare(version, self.requirements["<"]) < 0:
                    raise Plugin.Dependency.BadVersionError(
                        self.plugin.name(),
                        self.name,
                        version,
                        "<",
                        self.requirements["<"],
                    )
            if "<=" in self.requirements:
                if not apt_pkg.version_compare(version, self.requirements["<="]) <= 0:
                    raise Plugin.Dependency.BadVersionError(
                        self.plugin.name(),
                        self.name,
                        version,
                        "<=",
                        self.requirements["<="],
                    )

    class File:
        """File helper class.

        Holds a couple of values.
        """

        def __init__(self, path, content, plugin_name):
            self.path = path
            self.content = content
            self.backed_up = False
            self.written = False
            self.plugin_name = plugin_name

    def __init__(self, plugin_name, sjconf, conf):
        self.plugin_name = plugin_name
        self.sjconf = sjconf
        self.set_conf(conf)

    def name(self):
        """Returns plugin's name."""
        return self.plugin_name

    def version(self):
        """Returns plugin's version."""
        if hasattr(self.__class__, "VERSION"):
            return getattr(self.__class__, "VERSION")
        else:
            raise Plugin.MethodNotImplementedError(self.name(), "version")

    def dependencies(self):
        """List dependencies of this plugin.

        @returns: an iterable container of Dependency instances.
        """
        return ()

    def conf_types(self):
        """List of 3-tuple configuration option type mapping."""
        return ()

    def services_to_restart(self):
        """List of services to restart.

        The services listed therein will be restarted upon usage of the
        --restart command line switch with plugin's name as the argument.
        """
        return ()

    def services_to_reload(self):
        """List of services to reload.

        The services listed therein will be reloaded upon usage of the
        --reload command line switch with plugin's name as the argument.
        """
        return ()

    def conf_files_path(self):
        """List of configuration file path."""
        return ()

    def files_to_backup_path(self):
        return ()

    def conf_class(self):
        if hasattr(self.__class__, "Conf"):
            return getattr(self.__class__, "Conf")
        else:
            return Conf

    def conf_section_class(self):
        if hasattr(self.__class__, "Conf") and hasattr(
            getattr(
                self.__class__,
                "Conf",
            ),
            "ConfSection",
        ):
            return getattr(
                getattr(
                    self.__class__,
                    "Conf",
                ),
                "ConfSection",
            )
        elif hasattr(self.__class__, "ConfSection"):
            return getattr(self.__class__, "ConfSection")
        else:
            return Conf.ConfSection

    def set_conf(self, conf):
        if (self.conf_class() and conf.__class__ != self.conf_class()) or (
            self.conf_section_class()
            and self.conf_section_class() != conf.conf_section_class
        ):
            self.conf = self.conf_class()(
                conf, conf_section_class=self.conf_section_class()
            )
        else:
            self.conf = conf
        for conf_type in self.conf_types():
            self.conf.set_type(*conf_type)

    def file_content(self, file_path):
        """Generates content to be written to @file_path."""
        raise Plugin.MethodNotImplementedError(self.name(), "file_content")

    def conf_files(self):
        """Returns a list of Plugin.File instance of each config file"""
        return list(
            map(
                lambda file_path: Plugin.File(
                    file_path, self.file_content(file_path), self.name()
                ),
                self.conf_files_path(),
            )
        )

    def files_to_backup(self):
        return list(
            map(
                lambda file_path: Plugin.File(file_path, None, self.name()),
                self.files_to_backup_path(),
            )
        )


class PluginWithTemplate(Plugin):
    """Template based SJConf base plugin."""

    def template_path(self, file_path, confs_to_test=None):
        """Provide template path for @file_path configuration file.

        Attempt to get template path for @file_path from the following
        configuration keys in this order:
            * template_$(basename file_path)
            * template_$(basename file_path) without .conf occurences
            * template

        If @confs_to_test is provided, use it to get the template path
        from the key listed above.
        """
        if not confs_to_test:
            confs_to_test = (self.conf[self.name()],)
        for conf_to_test in confs_to_test:
            for key_to_test in (
                "template_" + os.path.basename(file_path),
                "template_" + os.path.basename(file_path).replace(".conf", ""),
                "template",
            ):
                if key_to_test in conf_to_test:
                    return self.sjconf.base_dir + "/" + conf_to_test[key_to_test]
        raise Plugin.MethodNotImplementedError(self.name(), "template_path")

    def template_conf(self, file_path):
        """Configuration to be used for @file_path's template.

        @returns: configuration dictionary to be used for @file_path template.
        """
        return self.conf[self.name()]

    def file_content(self, file_path):
        """Generates content to be written to @file_path.

        Uses template corresponding to @file_path.

        @see: Plugin.file_content
        """
        template_conf = self.template_conf(file_path)
        confs_to_test = [template_conf]
        if self.name() in self.conf:
            confs_to_test.append(self.conf[self.name()])
        template_path = self.template_path(file_path, confs_to_test)
        return open(template_path).read() % template_conf
