#!/usr/bin/python

import glob, setuptools

setuptools.setup(
        name = 'sjconf',
        version = '1.3.2',
        scripts = ['sjconf'],
        py_modules = ['sjconf'],
        packages = ['sjconfparts'],
        data_files = [('/etc/smartjog', glob.glob("conf/*.conf")), ('/etc/smartjog/base', glob.glob("conf/base/*")), ('/etc/smartjog/templates', glob.glob("conf/templates/*")), ('/etc/smartjog/custom', glob.glob("conf/custom/*")), ('/var/lib/sjconf/plugins', []), ('/var/lib/sjconf/', [])]
    )
