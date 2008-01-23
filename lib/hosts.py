#!/usr/bin/python

import os

SERVICE_NAME='hosts'
HOSTS_CONFFILE='/hosts'

conf_file = {}
hosts = []

def init(sjconf, base, local, config):
    global conf_file
    global hosts
    global HOSTS_CONFFILE

    HOSTS_CONFFILE  = sjconf['conf']['etc_dir'] + HOSTS_CONFFILE

    # We take the basic template and will update it later on demand
    conf_file = {
        'service'  : SERVICE_NAME,
        'restart'  : None,
        'path'     : os.path.realpath(HOSTS_CONFFILE),
        'content'  : open(sjconf['conf']['base_path'] + '/' + config['network:hosts_template'], 'r').read() % config}

def get_conf_files():
    global conf_file
    global hosts
    # Generating the custom part of the etc/hosts files with custom hosts plugins gave us
    conf_file['content'] += '\n# Custom hosts definitions\n' + '\n'.join(hosts) + '\n'
    # Only one configuration file for etc/hosts
    return [conf_file]

def custom_host(host, address):
    global hosts
    # Add a custom pair of address/host
    hosts += ["%s %s" % (address, host)]

def get_files_to_backup():
    # Ask sjconf to backup the /etc/hosts file
    if os.path.isfile(HOSTS_CONFFILE):
        return [{'service' : SERVICE_NAME,
                 'path'    : HOSTS_CONFFILE}]
    return []

def restore_files(to_restore):
    # Restore our files. Surely only one, /etc/hosts
    for file in list(to_restore):
        if file['service'] == SERVICE_NAME:
            if os.path.isfile(file['path']):
                os.unlink(file['path'])
            os.rename(file['backup_path'], file['path'])
            to_restore.remove(file)

def restart_service(sjconf, already_restarted):
    # No need to restart anything with etc/hosts
    return True
