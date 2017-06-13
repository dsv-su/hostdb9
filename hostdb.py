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

    def temp2(self):
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

    def temp(self):
        vlans = self.ipam.list_vlans()
        for vlan in vlans:
            vlan_ref = vlan['_ref']
            vlan_cidr = vlan['network']
            vlan_comment = vlan['comment']
            print('Vlan:', vlan_cidr, vlan_comment)
            for ip in self.ipam.list_vlan_ips(vlan_cidr):
                print('Host:', 
                      ip['ip_address'], 
                      ip['status'], 
                      ip['names'])
            print(self.ipam.create_host_auto(vlan_cidr, 'test.dsv.su.se'))
            print(self.ipam.create_alias('test.dsv.su.se', 
                                         'example.dsv.su.se'))
            for cname in self.ipam.list_cnames('dsv.su.se'):
                print('Cname:',
                      cname['canonical'],
                      cname['name'])
            print(self.ipam.delete_host('test.dsv.su.se'))
            print(self.ipam.delete_alias('example.dsv.su.se'))

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
        client.temp2()
    else:
        client.temp()

