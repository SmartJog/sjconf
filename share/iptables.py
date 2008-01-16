#!/usr/bin/python

import os

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
    if "iptables" not in already_restarted:
        already_restarted += ["iptables"]
        return os.system("/etc/init.d/ restart")
    return 0
