#!/usr/bin/nosetests
# -*- coding: utf-8 -*-

import sys
import os
import unittest
import sjconf
import tempfile
import shutil
import pickle
import json

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

ENVIRONMENT_PLUGIN = '''\
# -*- coding: utf-8 -*-

import sjconf

class Plugin(sjconf.Plugin):

    VERSION = '6.6.6'

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
        return (self.sjconf.etc_dir + '/environment',)
'''


class TestClass:
    def setUp(self):
        self._tmpdir      = tempfile.mkdtemp(prefix='sjconftest_')
        self._etc         = self._tmpdir + '/etc'
        self._sjconf      = self._tmpdir + '/etc/sjconf'
        self._sjconf_conf = self._tmpdir + '/etc/sjconf/sjconf.conf'
        self._base_conf   = self._tmpdir + '/etc/sjconf/base.conf'
        self._local_conf  = self._tmpdir + '/etc/sjconf/local.conf'
        self._plugins     = self._tmpdir + '/var/lib/sjconf/plugins'
        self._environment = self._tmpdir + '/var/lib/sjconf/plugins/environment.py'

        os.makedirs(self._sjconf)
        open(self._base_conf, 'w').write(BASE_CONF)
        open(self._local_conf, 'w').write(LOCAL_CONF)
        open(self._sjconf_conf, 'w').write(SJCONF_CONF % {
            'tmpdir': self._tmpdir,
            'etc_dir' : self._etc,
            'base_dir' : self._sjconf,
            'plugins_path': self._plugins,
        })

        os.makedirs(self._plugins)
        open(self._environment, 'w').write(ENVIRONMENT_PLUGIN)

        self.conf = sjconf.SJConf(sjconf_file_path = self._sjconf_conf)
        self.conf.plugin_enable('environment')

    def tearDown(self):
        shutil.rmtree(self._tmpdir)

    def test_01_regular_deploy(self):
        self.conf.deploy_conf(backup = False)
        environment = file(self.conf.etc_dir + '/environment', 'rb').read(4096)
        assert environment == 'PATH="/bin:/usr/bin"\n'

    def test_02_set(self):
        self.conf.set('environment', 'paths', '/tmp    ,    /bin')
        assert self.conf.conf_typed()['environment']['paths'] == ['/tmp', '/bin']

        self.conf.deploy_conf(backup = False)
        environment = file(self.conf.etc_dir + '/environment', 'rb').read(4096)
        assert environment == 'PATH="/tmp:/bin"\n'

    def test_03_list_add(self):
        self.conf.list_add('environment', 'paths', '/usr/local/bin')
        assert self.conf.conf_typed()['environment']['paths'] == ['/bin', '/usr/bin', '/usr/local/bin']

        self.conf.deploy_conf(backup = False)
        environment = file(self.conf.etc_dir + '/environment', 'rb').read(4096)
        assert environment == 'PATH="/bin:/usr/bin:/usr/local/bin"\n'

    def test_04_list_remove(self):
        self.conf.list_remove('environment', 'paths', '/bin')
        assert self.conf.conf_typed()['environment']['paths'] == ['/usr/bin']

        self.conf.deploy_conf(backup = False)
        environment = file(self.conf.etc_dir + '/environment', 'rb').read(4096)
        assert environment == 'PATH="/usr/bin"\n'

    def test_05_pickle_conf_typed(self):
        typed_conf = self.conf.conf_typed()
        unpickled = pickle.loads(pickle.dumps(typed_conf))
        assert typed_conf == unpickled

    def test_06_json_conf_typed(self):
        typed_conf = self.conf.conf_typed()
        unjsoned = json.loads(json.dumps(typed_conf))
        assert typed_conf == unjsoned
