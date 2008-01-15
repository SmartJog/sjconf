#!/usr/bin/python

from pprint import pprint

def init(sjconf, base, local, config):
    print open(sjconf["conf"]["base_path"] + "/" + config["vpn:template"], "r").read() % config

    for i in config["network:inter_vpns"].split(","):
        intervpn = dict(base["intervpn"])
        intervpn.update(local[i])
        print open(sjconf["conf"]["base_path"] + "/" + intervpn["template"], "r").read() % \
            dict(map(lambda key: ("intervpn:" + key, intervpn[key]) , intervpn.keys()))

