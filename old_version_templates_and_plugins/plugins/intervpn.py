#!/usr/bin/python

from pprint import pprint

import os
import time
import hosts
#import shaping

SERVICE_NAME='intervpn'
INTERVPN_CONFDIR='/intervpn/'
DEFAULT_INTERVPN_CONFDIR='/default/intervpn'

INITD='/init.d/intervpn'


conf_files = []

def init(sjconf, base, local, config):
    global conf_files, INTERVPN_CONFDIR, DEFAULT_INTERVPN_CONFDIR, INITD

    INTERVPN_CONFDIR = sjconf['conf']['etc_dir'] + INTERVPN_CONFDIR
    DEFAULT_INTERVPN_CONFDIR = sjconf['conf']['etc_dir'] + DEFAULT_INTERVPN_CONFDIR

    conf_files = []

    # No inter-rxtx vpn, returning
    if not config['network:intervpns'].strip():
        return

    # Iterate on all inter-rxtx vpns
    for i in config['network:intervpns'].split(','):

        # Copying base dict because we are going to modify it
        base_conf = dict(base['intervpn'])
        base_conf.update(local[i])
        # Copying config dict because we are going to modify it
        intervpn = dict(config)
        intervpn.update(dict(map(lambda key: ('intervpn:' + key, base_conf[key]) , base_conf.keys())))

        conf_files += [{
            'service'  : SERVICE_NAME,
            'restart'  : INITD,
            'path'     : os.path.realpath('%s/%s.conf' % (INTERVPN_CONFDIR, i)),
            'content'  : open(sjconf['conf']['base_path'] + '/' + intervpn['intervpn:template'], 'r').read() % intervpn}]

        # Ask hosts service to add a host to this file
        hosts.custom_host(intervpn['intervpn:remote_peer_hostname'], intervpn['intervpn:remote_peer'])


# We ask for sjconf to move from the way and backup all files that are not .key or .crt
def get_files_to_backup():
    to_backup = []

    if not os.path.isdir(INTERVPN_CONFDIR):
        return to_backup

    for file in os.listdir(INTERVPN_CONFDIR):
        if os.path.isfile(INTERVPN_CONFDIR + '/' + file):
            if not (file.endswith('.crt') or file.endswith('.key')):
                to_backup += [{'service' : SERVICE_NAME,
                               'path'    : INTERVPN_CONFDIR + '/' + file}]
    return to_backup

def restart_service(sjconf, already_restarted):
    global INITD

    if SERVICE_NAME not in already_restarted:
        INITD = sjconf['conf']['etc_dir'] + INITD
        already_restarted += [SERVICE_NAME]
        print "Restarting service: %s" % (SERVICE_NAME)
        if os.system('%s restart' % (INITD)):
            return False
        # Sleep 5 seconds to let intervpn some time to create tun devices (for shaping)
        #time.sleep(5)
        # A vpn tun device may be shaped, restasrting shaping service
        #if not shaping.restart_service(sjconf, already_restarted):
        #    return False
        # We need to update hosts as some garbage may remain or host be missing
        if not hosts.restart_service(sjconf, already_restarted):
            return False
    return True

def get_conf_files():
    global conf_files
    return conf_files