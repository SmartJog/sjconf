#!/usr/bin/python

from pprint import pprint

import os
import time
import iptables
import hosts

SERVICE_NAME='openvpn'
OPENVPN_CONFDIR='/etc/openvpn/'

INITD='/etc/init.d/openvpn'

conf_files = []

def init(sjconf, base, local, config):
    global conf_files

    conf_files = [{
        'service'  : SERVICE_NAME,
        'restart'  : INITD,
        'path'     : os.path.realpath('%s/%s.conf' % (OPENVPN_CONFDIR, local['rxtx']['hostname'])),
        'content'  : open(sjconf['conf']['base_path'] + '/' + config['vpn:template'], 'r').read() % config
        }]

    if not config['network:intervpns'].strip():
        return

    for i in config['network:intervpns'].split(','):

        base_conf = dict(base['intervpn-%s' % local[i]['mode']])
        base_conf.update(local[i])
        intervpn = dict(config)
        intervpn.update(dict(map(lambda key: ('intervpn:' + key, base_conf[key]) , base_conf.keys())))

        conf_files += [{
            'service'  : SERVICE_NAME,
            'restart'  : INITD,
            'path'     : os.path.realpath('%s/%s.conf' % (OPENVPN_CONFDIR, i)), \
            'content'  : open(sjconf['conf']['base_path'] + '/' + intervpn['intervpn:template'], 'r').read() % intervpn}]

        if local[i]['mode'] == 'server':
            iptables.custom_rule(open(sjconf['conf']['base_path'] + '/' + intervpn['intervpn:iptables_template'], 'r').read() % intervpn)
        hosts.custom_host(intervpn['intervpn:remote_peer_hostname'], intervpn['intervpn:remote_peer'])

def get_conf_files():
    global conf_files
    return conf_files


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
        ret = os.system('%s restart' % INITD)
        time.sleep(5)
        hosts.restart_service(already_restarted)
        return ret
    return 0
