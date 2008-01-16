#!/usr/bin/python

import os

SERVICE_NAME="iptables"
INITD="/etc/init.d/iptables"

def init(sjconf, base, local, conf):
    return []

def save_confs():
    pass

def apply_confs():
    pass

def rollback_confs():
    pass

def get_files_to_backup():
    to_backup = []
    return to_backup

def restore_files(to_restore):
    pass

def restart_service(already_restarted):
    if SERVICE_NAME not in already_restarted:
        already_restarted += [SERVICE_NAME]
        return os.system("%s restart" % INITD)
    return 0
