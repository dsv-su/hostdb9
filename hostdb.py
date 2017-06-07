#!/usr/bin/env python3
# coding=utf-8

import argparse, configparser
import infoblox

class Hostdb9:
    def __init__(self, args, conf):
        self.verbose = args.verbose
        self.ipam = infoblox.Infoblox(conf['server'])

    def execute(self, command):
        pass

    def temp(self):
        vlans = self.ipam.list_vlans()
        for vlan in vlans:
            print('Vlan:', vlan['network'], vlan['comment'])
        print('Count:', len(vlans))
        records = self.ipam.search({'name~':'.',
                                    'zone': 'dsv.su.se',
                                    '_return_fields+': 'record'})
        types = set()
        for record in records:
            types.add(record['type'])
            if record['type'] == 'UNSUPPORTED':
                print(record)
            else:
                print(record['type'],
                      record['name'] + '.' + record['zone'])
        print('types:', types)
        print('Count:', len(records))


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

    client = Hostdb9(args, conf)
    
    if args.command:
        client.execute(command)
    else:
        client.temp()

