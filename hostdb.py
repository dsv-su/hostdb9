#!/usr/bin/env python3

import sys, argparse
import infoblox

def usage():
    print('Usage.')

def run():

    ipam = infoblox.Infoblox('config.ini')
    print(ipam.do('').text)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', help="the command to run against the ipam server")
    
    run(parser.parse_args())
