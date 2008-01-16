#!/usr/bin/python

from pprint import pprint

import os
import iptables

SERVICE_NAME='openvpn'
OPENVPN_CONFDIR='/etc/openvpn/'

INITD='/etc/init.d/openvpn'

def init(sjconf, base, local, config):
    new_confs = [{
        'service'  : SERVICE_NAME,
        'restart'  : INITD,
        'path'     : os.path.realpath('%s/%s.conf' % (OPENVPN_CONFDIR, local['rxtx']['hostname'])),
        'content'  : open(sjconf['conf']['base_path'] + '/' + config['vpn:template'], 'r').read() % config
        }]

    for i in config['network:intervpns'].split(','):
        if i == '':
            continue
        intervpn = dict(base['intervpn'])
        intervpn.update(local[i])
        new_confs += [{
            'service'  : SERVICE_NAME,
            'restart'  : INITD,
            'path'     : os.path.realpath('%s/%s.conf' % (OPENVPN_CONFDIR, i)), \
            'content'  : open(sjconf['conf']['base_path'] + '/' + intervpn['template'], 'r').read() % 
                dict(map(lambda key: ('intervpn:' + key, intervpn[key]) , intervpn.keys()))}]
    return new_confs

def get_files_to_backup():
    to_backup = []
    for file in os.listdir(OPENVPN_CONFDIR):
        if os.path.isfile(OPENVPN_CONFDIR + '/' + file):
            if not (file.endswith('.crt') or file.endswith('.key')):
                to_backup += [{'service' : SERVICE_NAME,
                               'path'    : OPENVPN_CONFDIR + '/' + file}]
    return to_backup

def restore_files(to_restore):
    for file in os.listdir(OPENVPN_CONFDIR):
        path = os.path.isfile(OPENVPN_CONFDIR + '/' + file)
        if os.path.isfile(path):
            if not (file.endswith('.crt') or file.endswith('.key')):
                os.unlink(path)

    for file in list(to_restore):
        if file['service'] == SERVICE_NAME:
            os.rename(file['backup_path'], file['path'])
            to_restore.remove(file)

def save_confs():
    pass

def apply_confs():
    pass

def rollback_confs():
    pass

def restart_service(already_restarted):
    iptables.restart_service(already_restarted)
    if SERVICE_NAME not in already_restarted:
        already_restarted += [SERVICE_NAME]
        print "Restarting service: %s" % (SERVICE_NAME)
        return os.system('%s restart' % INITD)
    return 0
