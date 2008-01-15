#!/usr/bin/python

import ConfigParser
from pprint import pprint

LOCAL_FILE="/etc/smartjog/local.ini"
BASE_FILE="/etc/smartjog/base.ini"

def load_init(filename):
    cp = ConfigParser.RawConfigParser()
    cp.read(filename)
    dic = {}
    for section in cp.sections():
        for key, value in cp.items(section):
            dic['%s:%s' % (section, key)] = value
    return dic

base = load_init(BASE_FILE)
local = load_init(LOCAL_FILE)

config=dict(base)
config.update(local)

pprint(config)

