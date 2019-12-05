#!/usr/bin/nosetests
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import unittest

import sjconf
from sjconfparts.plugin import Plugin

SJCONF_CONF = """\
[conf]
backup_dir = %(tmpdir)s/var/backups/sjconf/
base_dir = %(base_dir)s
etc_dir = %(etc_dir)s
plugins =
plugins_path = %(plugins_path)s
templates_path = %(tmpdir)s/etc/sjconf/templates/
"""

LOCAL_CONF = """\
[environment]
paths = /bin, /usr/bin
"""

BASE_CONF = """\
[environment]
paths =
"""

PLUGIN = """\
# -*- coding: utf-8 -*-

import sjconf

class Plugin(sjconf.Plugin):

    VERSION = '0.42.0'

    class Error(sjconf.Plugin.Error):
        pass

    def conf_types(self):
        return (
            (self.name(), 'paths', 'list'),
        )

    def file_content(self, file_path):
        content  = ''
        content += "PATH=\\"" + ':'.join(self.conf[self.name()]['paths_list']) + "\\"\\n"
        return content

    def conf_files_path(self):
        return (self.sjconf.etc_dir + '/plugin',)
"""


class TestPlugin(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="sjconftest_")
        self._etc = self._tmpdir + "/etc"
        self._sjconf = self._tmpdir + "/etc/sjconf"
        self._sjconf_conf = self._tmpdir + "/etc/sjconf/sjconf.conf"
        self._base_conf = self._tmpdir + "/etc/sjconf/base.conf"
        self._local_conf = self._tmpdir + "/etc/sjconf/local.conf"
        self._plugins = self._tmpdir + "/var/lib/sjconf/plugins"
        self._plugin = self._tmpdir + "/var/lib/sjconf/plugins/plugin.py"

        os.makedirs(self._sjconf)
        open(self._base_conf, "w").write(BASE_CONF)
        open(self._local_conf, "w").write(LOCAL_CONF)
        open(self._sjconf_conf, "w").write(
            SJCONF_CONF
            % {
                "tmpdir": self._tmpdir,
                "etc_dir": self._etc,
                "base_dir": self._sjconf,
                "plugins_path": self._plugins,
            }
        )

        os.makedirs(self._plugins)
        open(self._plugin, "w").write(PLUGIN)

        self.conf = sjconf.SJConf(sjconf_file_path=self._sjconf_conf)
        self.conf.plugin_enable("plugin")
        self.plugin = self.conf.plugins()["plugin"]

    def tearDown(self):
        shutil.rmtree(self._tmpdir)

    def test_01_plugin_dependencies_eq(self):
        dep = self.plugin.Dependency(self.plugin, "test", requirements={"=": "0.9.1"})
        self.assertRaises(Plugin.Dependency.BadVersionError, dep.verify, "0.42.11")

    def test_02_plugin_dependencies_gt(self):
        dep = self.plugin.Dependency(self.plugin, "test", requirements={">": "0.9.1"})
        self.assertRaises(Plugin.Dependency.BadVersionError, dep.verify, "0.9.1")

    def test_03_plugin_dependencies_gte(self):
        dep = self.plugin.Dependency(self.plugin, "test", requirements={">=": "0.9.1"})
        self.assertRaises(Plugin.Dependency.BadVersionError, dep.verify, "0.9.0")
        self.assertRaises(Plugin.Dependency.BadVersionError, dep.verify, "0.9.1~dev")

    def test_04_plugin_dependencies_lt(self):
        dep = self.plugin.Dependency(self.plugin, "test", requirements={"<": "0.9.1"})
        self.assertRaises(Plugin.Dependency.BadVersionError, dep.verify, "0.9.1")

    def test_05_plugin_dependencies_lte(self):
        dep = self.plugin.Dependency(self.plugin, "test", requirements={"<=": "0.9.1"})
        self.assertRaises(Plugin.Dependency.BadVersionError, dep.verify, "0.9.2")
        self.assertRaises(Plugin.Dependency.BadVersionError, dep.verify, "0.9.1+bpo")
