#!/usr/bin/python

from pprint import pprint

import os

SERVICE_NAME='shaping'
SHAPING_CONFFILE='/etc/default/sjshaping'

INITD='/etc/init.d/sjnetworking shaping-'

conf_file = None
shapes = []

def init(sjconf, base, local, config):
    global conf_file
    global shapes

    if not config['network:shaping'].strip():
        return

    conf_file = {
        'service'  : SERVICE_NAME,
        'restart'  : INITD,
        'path'     : os.path.realpath(SHAPING_CONFFILE), \
        'content'  : ''}

    for i in config['network:shaping'].split(','):

        base_conf = dict(base['shaping'])
        base_conf.update(local[i])
        shaping = dict(config)
        shaping.update(dict(map(lambda key: ('shaping:' + key, base_conf[key]) , base_conf.keys())))
        shapes += [open(sjconf['conf']['base_path'] + '/' + shaping['shaping:template'], 'r').read() % shaping]

def get_conf_files():
    global conf_file
    if not conf_file:
        return []
    conf_file['content'] += '\n\n'.join(shapes)
    return [conf_file]


def save_confs():
    pass

def apply_confs():
    pass

def rollback_confs():
    pass

def get_files_to_backup():
    if os.path.isfile(SHAPING_CONFFILE):
        return [{'service' : SERVICE_NAME,
                 'path'    : SHAPING_CONFFILE}]
    return []

def restore_files(to_restore):
    pprint(to_restore)
    for file in list(to_restore):
        if file['service'] == SERVICE_NAME:
            if os.path.isfile(file['path']):
                os.unlink(file['path'])
            os.rename(file['backup_path'], file['path'])
            to_restore.remove(file)

def restart_service(already_restarted):
    if SERVICE_NAME not in already_restarted:
        already_restarted += [SERVICE_NAME]
        return os.system(INITD + "restart")
    return 0
