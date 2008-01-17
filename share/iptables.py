#!/usr/bin/python

import os, pprint

SERVICE_NAME="iptables"
INITD="/etc/init.d/iptables"
IPTABLES_CONFFILE="/etc/default/sjiptables"

custom_rules = []
conf_file = {}

def init(sjconf, base, local, config):
    global conf_file

    conf_file = {
        'service'  : SERVICE_NAME,
        'restart'  : INITD,
        'path'     : os.path.realpath(IPTABLES_CONFFILE),
        'content'  : open(sjconf['conf']['base_path'] + '/' + config['iptables:template'], 'r').read() % config
        }

def custom_rule(rule):
    global custom_rules
    custom_rules += [rule]

def get_conf_files():
    global conf_file
    conf_file['content'] += '\n' + '#Custom tules\n'  + '\n'.join(custom_rules)
    return [conf_file]

def save_confs():
    pass

def apply_confs():
    pass

def rollback_confs():
    pass

def get_files_to_backup():
    if os.path.isfile(IPTABLES_CONFFILE):
        return [{'service' : SERVICE_NAME,
                 'path'    : IPTABLES_CONFFILE}]
    return []

def restore_files(to_restore):
    pprint(to_restore)
    for file in list(to_restore):
        if file['service'] == SERVICE_NAME:
            if os.path.isfile(file['path']):
                os.unlink(file['path'])
            os.rename(file['backup_path'], file['path'])
            to_restore.remove(file)
    pprint(to_restore)

def restart_service(already_restarted):
    if SERVICE_NAME not in already_restarted:
        already_restarted += [SERVICE_NAME]
        return os.system("%s restart" % INITD)
    return 0
