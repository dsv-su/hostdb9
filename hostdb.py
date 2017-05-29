#!/usr/bin/env python3

import argparse, configparser
import infoblox

class hostdb9:
    def __init__(self, args, conf):
        self.verbose = args.verbose
        self.client = conf['server']
        self.ipam = infoblox.Infoblox(self.client['baseurl'],
                                      self.client['user'],
                                      self.client['password'])

    def execute(self, command):
        pass

    def format(self, response, *fields):
        return {str(field) : response[field]
                for field in response
                if field in fields}

    def interact(self):
        vlans = self.ipam.list_vlans()
        for vlan in vlans:
            print('Vlan:', vlan['network'], vlan['comment'])
        print('Count:', len(vlans))
        records = self.ipam.search({'name~':'.',
                                    'zone': 'dsv.su.se',
                                    '_return_fields+': 'record'})
        for record in records:
            if record['type'] == 'UNSUPPORTED':
                print(self.ipam.get(record['record']['_ref']))
            else:
                print(record['type'],
                      record['name'] + '.' + record['zone'])
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

    client = hostdb9(args, conf)
    
    if args.command:
        client.execute(command)
    else:
        client.interact()

'''
        self.execute_temp('get',
                          'zone_auth',
                          params=[('_return_fields', 'address')])
        self.execute_temp('get',
                          'record:host',
                          params=[('_paging', 1),
                                  ('_max_results', 1000),
                                  ('_return_as_object', 1)])
'''
