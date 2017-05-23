#!/usr/bin/env python3

import argparse, configparser
import infoblox

class hostdb9:
    def __init__(self, args, conf):
        self.verbose = args.verbose
        self.client = conf['client']
        self.ipam = infoblox.Infoblox(self.client['baseurl'],
                                      self.client['user'],
                                      self.client['password'])

    def execute(self, command):
        pass

    def execute_temp(self, method, path, params=None):
        r = self.ipam.req(method, path, params=params)
        print(r.status_code)
        if self.verbose: print(r.text)

    def interact(self):
        self.execute_temp('get', '', params=[('_schema', '')])
        self.execute_temp('get', 'network')
        self.execute_temp('get', 'zone_auth', [('_return_fields', 'address')])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
                        action  = 'count',
                        default = 0,
                        help    ='enable verbose output')
    parser.add_argument('command', 
                        nargs   = '?',
                        default = None,
                        help    = 'the command to run against the ipam server')
    args = parser.parse_args()

    conf = configparser.ConfigParser()
    conf.read('config.ini')

    client = hostdb9(args, conf)
    
    if args.command:
        client.execute(command)
    else:
        client.interact()
