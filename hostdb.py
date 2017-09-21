#!/usr/bin/env python3
# coding=utf-8

import argparse, configparser, os
import client, dns_parser, dns_reader, errors

class Hostdb9:
    def __init__(self, args, conf):
        self.client = client.Client(conf['server'])
        myconf = conf['client']
        zonedir = myconf['zonedir']
        if not zonedir.endswith('/'):
            zonedir += '/'
        self.zonedir = zonedir
        self.domain = myconf['tld']
        self.confirm = myconf.getboolean('ask_questions')
        self.verbose = args.verbose

    def execute(self, commandlist):
        command = commandlist[0]
        args = commandlist[1:]
        if command == 'dump':
            self.dump_state()
        elif command == 'update':
            self.update()
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

    def update(self):
        try:
            import pprint
            parser = dns_parser.Parser(self.domain)
            for item in os.listdir(self.zonedir):
                if item.endswith('.conf'):
                    with open(self.zonedir + item, 'r') as f:
                        parser.parse(f)
            target = parser.get_state()
            parser.clear_state()
            read_conf = dns_reader.read(self.client, self.domain)
            state = parser.parse(read_conf)
            if self.verbose:
                print("State:")
                pprint.pprint(state)
                print("Target:")
                pprint.pprint(target)
            actions = self.client.diff(state, target)
            if self.confirm:
                print("Changes:")
                pprint.pprint(actions)
                ans = input("Are you sure you want to make these changes? [Y/n]\n").lower()
                if ans not in ('yes', 'y', ''):
                    print('Aborting.')
                    return
            print('Making requested changes')
            self.client.execute(actions)
        except errors.ClientError as e:
            if isinstance(e, errors.ParserError):
                print('A parsing error occurred while processing a '+ e.context +' line:')
            elif isinstance(e, errors.IpamError):
                print('An error occurred when communicating with the server:')
            print(e.message)
            if self.confirm:
                ans = input("Do you want to see the complete exception? [y/N]\n").lower()
                if ans not in ('no', 'n', ''):
                    import traceback
                    print(traceback.format_exc())


    def dump_state(self):
        for line in dns_reader.read(self.client, self.domain):
            print(line)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
                        action  = 'count',
                        default = 0,
                        help    = 'enable verbose output')
    parser.add_argument('command',
                        nargs   = '*',
                        default = None,
                        help    = 'the command to run')
    args = parser.parse_args()
    conf = configparser.ConfigParser()
    conf.read('config.ini')
    client = Hostdb9(args, conf)
    if args.command:
        client.execute(args.command)
    else:
        client.interact()

