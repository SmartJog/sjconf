#!/usr/bin/python

from distutils.core import setup
import glob

setup(
        name = 'sjconf',
        version = '1.0.0',
        scripts = ['sjconf'],
        py_modules = ['sjconf'],
        packages = ['sjconfparts'],
        data_files = [('/etc/smartjog', glob.glob("conf/*.conf")), ('/etc/smartjog/base', glob.glob("conf/base/*")), ('/etc/smartjog/templates', glob.glob("conf/templates/*")), ('/etc/smartjog/custom', glob.glob("conf/custom/*")), ('/var/lib/sjconf/plugins', []), ('/var/lib/sjconf/', [])]
    )
