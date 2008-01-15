#!/usr/bin/python

def init(sjconf, base, local, conf):
    print open(sjconf["conf:base_path"] + "/" + conf["vpn:template"], "r").read() % conf

