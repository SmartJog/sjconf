#!/usr/bin/python

from pprint import pprint

import os

SERVICE_NAME='shaping'
HOSTS_CONFFILE='/etc/hosts'

conf_file = {}
hosts = []

def init(sjconf, base, local, config):
    global conf_file
    global hosts

    if not config['network:shaping'].strip():
        return


    conf_file = {
        'service'  : SERVICE_NAME,
        'restart'  : None,
        'path'     : os.path.realpath(HOSTS_CONFFILE), \
        'content'  : open(sjconf['conf']['base_path'] + '/' + config['network:hosts_template'], 'r').read() % config}

def get_conf_files():
    global conf_file
    global hosts
    conf_file['content'] += '\n# Custom hosts definitions\n' + '\n'.join(hosts) + '\n'
    return [conf_file]

def custom_host(host, address):
    global hosts
    hosts += ["%s %s" % (address, host)]

def save_confs():
    pass

def apply_confs():
    pass

def rollback_confs():
    pass

def get_files_to_backup():
    if os.path.isfile(HOSTS_CONFFILE):
        return [{'service' : SERVICE_NAME,
                 'path'    : HOSTS_CONFFILE}]
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
    pass
