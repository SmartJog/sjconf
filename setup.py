#!/usr/bin/python

from distutils.core import setup
import glob

setup(
        name = 'sjconf',
        version = '1.0.0~dev',
        scripts = ['sjconf'],
        py_modules = ['sjconf'],
        data_files = [('/etc/smartjog', glob.glob("conf/*.conf")), ('/etc/smartjog/templates', glob.glob("conf/templates/*")), ('/etc/smartjog/custom', glob.glob("conf/custom/*")), ('/usr/lib/sjconf/plugins', []), ('/var/lib/sjconf/', [])]
    )
