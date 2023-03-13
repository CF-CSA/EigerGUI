#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 17:21:54 2022

@author: Tim Gruene
"""

import json
import requests

"""
Basic command for the SIMPLON API of Dectris detectors
"""
class DetectorBackend:
    def __init__(self, ip, vers, port = 80):
        self.ip_ = ip
        self.version_ = vers
        self.port_ = port


    """
    Detector configuration
    'iface' can be detector, filewriter, stream, 
    Generic configuration command
    """
    def set_config(self, param, value, iface = 'detector'):
        url = 'http://%s:%s/%s/api/%s/config/%s' % (self.ip_, self.port_, iface, self.version_, param)
        self._request(url, data = json.dumps({'value': value}))
        
    def get_config(self, param, iface):
        # url = 'http://%s:%s/%s/api/%s/config/%s' % (self.ip_, self.port_, iface, self.version_, param)
        url = f"http://{self.ip_}:{self.port_}/{iface}/api/{self.version_}/config/{param}"
        reply = requests.get(url)
        val   = reply.json()['value']
        return val

    def get_status(self, param, iface):
        url = f"http://{self.ip_}:{self.port_}/{iface}/api/{self.version_}/status/{param}"
        reply = requests.get(url)
        val = reply.json()['value']
        return val

    def get_allowed(self, param, iface):
        url = 'http://%s:%s/%s/api/%s/config/%s' % (self.ip_, self.port_, iface, self.version_, param)
        reply = requests.get(url)
        val   = reply.json()['allowed_values']
        return val

    """
    Detector Commands:
        arm, trigger,disarm, cancel, initialize
    """
    def send_command(self, command, iface="detector"):
        url = f'http://{self.ip_}:{self.port_}/{iface}/api/{self.version_}/command/{command}'
        json_reply = self._request(url)
        return json_reply
        
    def _request(self, url, data={}, headers={"Content-Type": "application/json"}):
        reply = requests.put(url, data=data, headers=headers)
        assert reply.status_code in range(200, 300), reply.reason
        # https://python-forum.io/thread-27907.html
        try:
            reply = reply.json()
        except json.decoder.JSONDecodeError:
            reply = json.dumps({'value': -1})
        return reply
            
            
if __name__ == '__main__':
    print ("error: DetectorBackend should be imported and not run individually\n")
    exit(1)
