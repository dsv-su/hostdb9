#!/usr/bin/env python3
# coding=utf-8

import argparse, configparser
import client, errors

class Hostdb9:
    def __init__(self, args, conf):
        self.verbose = args.verbose
        self.client = client.Client(conf['server'])

    def execute(self, command):
        if command == ['test']:
            self.test()
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
            self.execute([command])

    def test(self):
        print('Listing vlans...')
        vlans = self.client.list_vlans()
        vlan = vlans[0]
        vlan_ref = vlan['_ref']
        vlan_cidr = vlan['network']
        vlan_comment = vlan['comment']
        print('Vlan:', vlan_cidr, vlan_comment)
        try:
            print('Creating host...')
            print(self.client.create_host_auto(vlan_cidr,
                                               'test.dsv.su.se',
                                               'AA:BB:CC:DD:EE:FF'))
        except errors.ClientError as e:
            print(e.message)
        try:
            print('Creating cname...')
            print(self.client.create_cname('test.dsv.su.se',
                                           'example.dsv.su.se'))
        except errors.ClientError as e:
            print(e.message)
        print('Listing cnames...')
        for cname in self.client.list_cnames('test.dsv.su.se'):
            print('Cname:',
                  cname['canonical'],
                  cname['name'])
        try:
            print('Creating dhcp ranges...')
            print(self.client.create_dhcp_range('193.10.8.40', '193.10.8.43'))
            print(self.client.create_dhcp_range('193.10.8.44', '193.10.8.46'))
        except errors.ClientError as e:
            print(e.message)
        for ip in self.client.list_vlan_ips(vlan_cidr):
            print('Host:',
                  ip['ip_address'],
                  ip['status'],
                  ip['names'])
        print('Listing dhcp ranges...')
        for ra in self.client.list_dhcp_ranges(vlan_cidr):
            print('Range:',
                  ra['start_addr'],
                  ra['end_addr'])
        try:
            print('Deleting dhcp ranges...')
            print(self.client.delete_dhcp_range('193.10.8.40', '193.10.8.43'))
            print(self.client.delete_dhcp_range('193.10.8.44', '193.10.8.46'))
        except errors.ClientError as e:
            print(e.message)
        try:
            print('Deleting host...')
            print(self.client.delete_host('test.dsv.su.se'))
        except errors.ClientError as e:
            print(e.message)
        try:
            print('Deleting cname...')
            print(self.client.delete_cname('example.dsv.su.se'))
        except errors.ClientError as e:
            print(e.message)
        print('Listing cnames...')
        for cname in self.client.list_cnames('handledning.dsv.su.se'):
            print('Cname:', cname['name'])
        print('Listing aliases...')
        result = self.client.list_iblox_aliases('mimas.dsv.su.se')
        for alias in result:
            print('Alias:', alias)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
                        action  = 'count',
                        default = 0,
                        help    = 'enable verbose output')
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

