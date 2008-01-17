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

    # main openvpn configuration file
    conf_files = [{
        'service'  : SERVICE_NAME,
        'restart'  : INITD,
        'path'     : os.path.realpath('%s/%s.conf' % (OPENVPN_CONFDIR, local['rxtx']['hostname'])),
        'content'  : open(sjconf['conf']['base_path'] + '/' + config['vpn:template'], 'r').read() % config
        }]

    # No inter-rxtx vpn, returning
    if not config['network:intervpns'].strip():
        return

    # Iterate on all inter-rxtx vpns
    for i in config['network:intervpns'].split(','):

        # Copying base dict because we are going to modify it
        base_conf = dict(base['intervpn-%s' % local[i]['mode']])
        base_conf.update(local[i])
        # Copying config dict because we are going to modify it
        intervpn = dict(config)
        intervpn.update(dict(map(lambda key: ('intervpn:' + key, base_conf[key]) , base_conf.keys())))

        conf_files += [{
            'service'  : SERVICE_NAME,
            'restart'  : INITD,
            'path'     : os.path.realpath('%s/%s.conf' % (OPENVPN_CONFDIR, i)), \
            'content'  : open(sjconf['conf']['base_path'] + '/' + intervpn['intervpn:template'], 'r').read() % intervpn}]

        if local[i]['mode'] == 'server':
            # server mode -> must open the approriate port on iptables
            iptables.custom_rule(open(sjconf['conf']['base_path'] + '/' + intervpn['intervpn:iptables_template'], 'r').read() % intervpn)

        # Ask hosts service to add a host to this file
        hosts.custom_host(intervpn['intervpn:remote_peer_hostname'], intervpn['intervpn:remote_peer'])

# We ask for sjconf to move from the way and backup all files that are not .key or .crt
def get_files_to_backup():
    to_backup = []
    for file in os.listdir(OPENVPN_CONFDIR):
        if os.path.isfile(OPENVPN_CONFDIR + '/' + file):
            if not (file.endswith('.crt') or file.endswith('.key')):
                to_backup += [{'service' : SERVICE_NAME,
                               'path'    : OPENVPN_CONFDIR + '/' + file}]
    return to_backup

# We restore files ourselves
def restore_files(to_restore):
    # Let's first remove any file except .crt and .key ones
    for file in os.listdir(OPENVPN_CONFDIR):
        path = os.path.isfile(OPENVPN_CONFDIR + '/' + file)
        if os.path.isfile(path):
            if not (file.endswith('.crt') or file.endswith('.key')):
                os.unlink(path)

    # And put back old files that are on the backup directory
    for file in list(to_restore):
        if file['service'] == SERVICE_NAME:
            os.rename(file['backup_path'], file['path'])
            to_restore.remove(file)

def restart_service(already_restarted):
    iptables.restart_service(already_restarted)
    if SERVICE_NAME not in already_restarted:
        already_restarted += [SERVICE_NAME]
        print "Restarting service: %s" % (SERVICE_NAME)
        ret = os.system('%s restart' % INITD)
        # Sleep 5 seconds to let openvpn some time to create tun devices (for shaping)
        time.sleep(5)
        # A vpn tun device may be shaped, restasrting shaping service
        shaping.restart_service(already_restarted)
        # We need to update hosts as some garbage may remain or host be missing
        hosts.restart_service(already_restarted)

def get_conf_files():
    global conf_files
    return conf_files
