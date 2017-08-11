#!/usr/bin/env python3
# coding=utf-8

import argparse, configparser
import infoblox

class Hostdb9:
    def __init__(self, args, conf):
        self.verbose = args.verbose
        ibloxconf = conf['server']
        self.iblox = infoblox.Infoblox(ibloxconf['baseurl'],
                                       ibloxconf['user'],
                                       ibloxconf['password'],
                                       bool(ibloxconf['verify_ssl']))
        self.client = infoblox.Client(self.iblox)

    def execute(self, command):
        if command == ['test']:
            self.temp()
        elif command == ['test2']:
            self.temp2()
        else:
            print(command)

    def interact(self):
        while True:
            command = 'exit'
            try:
                command = input('hostdb9> ')
            except EOFError as e:
                print(command)
                return
            if command == 'exit':
                return
            self.execute(command)

    def temp2(self):
        records = self.client.search({'name~': '.',
                                      'zone': 'dsv.su.se',
                                      '_return_fields+': 'record'})
        for record in records:
            if record['type'] == 'UNSUPPORTED':
                print(record)
            else:
                print(record['type'],
                      record['name'] + '.' + record['zone'])

    def temp(self):
        vlans = self.client.list_vlans()
        for vlan in vlans:
            vlan_ref = vlan['_ref']
            vlan_cidr = vlan['network']
            vlan_comment = vlan['comment']
            print('Vlan:', vlan_cidr, vlan_comment)
            for ip in self.client.list_vlan_ips(vlan_cidr):
                print('Host:', 
                      ip['ip_address'], 
                      ip['status'], 
                      ip['names'])
            try:
                print(self.client.create_host_auto(vlan_cidr, 
                                                   'test.dsv.su.se', 
                                                   'AA:BB:CC:DD:EE:FF'))
            except infoblox.ClientError as e:
                print(e.message)
            try:
                print(self.client.create_alias('test.dsv.su.se', 
                                               'example.dsv.su.se'))
            except infoblox.ClientError as e:
                print(e.message)
            for cname in self.client.list_cnames('dsv.su.se'):
                print('Cname:',
                      cname['canonical'],
                      cname['name'])
            try:
                print(self.client.delete_host('test.dsv.su.se'))
            except infoblox.ClientError as e:
                print(e.message)
            try:
                print(self.client.delete_alias('example.dsv.su.se'))
            except infoblox.ClientError as e:
                print(e.message)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
                        action  = 'count',
                        default = 0,
                        help    ='enable verbose output')
    parser.add_argument('command', 
                        nargs   = '*',
                        default = None,
                        help    = 'the command to run against the ipam server')
    args = parser.parse_args()

    conf = configparser.ConfigParser()
    conf.read('config.ini')

    client = Hostdb9(args, conf)
    
    if args.command:
        client.execute(args.command)
    else:
        client.interact()

