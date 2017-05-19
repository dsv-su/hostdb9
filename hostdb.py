#!/usr/bin/env python3

import sys, argparse, configparser
import infoblox

def run(args, conf):
    
    client = conf['client']
    ipam = infoblox.Infoblox(client['baseurl'], 
                             (client['user'], client['password']))
    print(ipam.do('').text)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', 
                        action  = 'count',
                        default = 0,
                        help    ='enable verbose output')
    parser.add_argument('command', 
                        help='the command to run against the ipam server')
    args = parser.parse_args()
    
    conf = configparser.ConfigParser()
    conf.read('config.ini')
    
    run(args, conf)
