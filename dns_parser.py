# coding=utf-8

import ipaddress
import errors

def parse(filename, commentstring):
    parser = Parser()
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith(commentstring):
                print('Warning! This comment will be lost: ' + line)
                continue
            if len(line) == 0:
                continue
            command = line
            comment = None
            if commentstring in line:
                [command, comment] = line.split(commentstring, maxsplit=1)
            parts = command.split()
            try:
                handler = getattr(parser, parts[0])
                handler(*parts[1:], comment=comment)
            except AttributeError as e:
                raise errors.ParserError('directive', 'Invalid directive: ' + parts[0])
    return parser.state_dict

class Parser(object):
    def __init__(self):
        self.state_dict = {}
        self.current_net = None
        self.current_net_obj = None
        self.current_ip = None
        self.current_ip_obj = None
        self.current_cname = None

    def __require_net(self, context, obj):
        if self.current_net_obj is None:
            raise errors.ParserError(context, obj + ': Unable to determine network parent')

    def __require_ip(self, context, obj):
        self.__require_net(context, obj)
        if self.current_ip_obj is None:
            raise errors.ParserError(context, obj + ': Unable to determine ip address parent')

    def __require_unique_name(self, context, name):
        for category, content in self.state_dict.items():
            if category == 'cnames':
                for cname in content:
                    if cname == name:
                        canonical = content[cname]['canonical']
                        err_msg = name + ': This name is already an alias for ' + canonical
                        raise errors.ParserError(context, err_msg)
            elif category == 'networks':
                for network, hosts in content.items():
                    for addr, data in hosts.items():
                        if 'name' in data and data['name'] == name:
                            err_msg = name + ': This name is already a canonical name'
                            raise errors.ParserError(context, err_msg)
                        if 'cnames' in data:
                            for addr_alias in data['cnames']:
                                if addr_alias['cname'] == name:
                                    err_msg = name + ': This name is already an alias for ' + data['name']
                                    raise errors.ParserError(context, err_msg)

    def network(self, cidr=None, comment=None):
        if cidr is None:
            raise errors.ParserError('network', 'No network address provided')
        if 'networks' not in self.state_dict:
            self.state_dict['networks'] = {}
        net_dict = self.state_dict['networks']
        if cidr in net_dict:
            raise errors.ParserError('network', cidr + ': This network is already defined')
        net_dict[cidr] = {}
        if comment is not None:
            net_dict[cidr]['comment'] = comment
        self.current_net = cidr
        self.current_net_obj = ipaddress.ip_network(cidr)

    def host(self, addr=None, name=None, mac=None, comment=None):
        if addr is None:
            raise errors.ParserError('host', 'No host address provided')
        self.__require_net('host', addr)
        if name in ['dhcp', 'reserved']:
            name = name + '-' + addr.replace('.', '-')
        if name is not None:
            self.__require_unique_name('host', name)
        elif mac is not None or comment is not None:
            raise errors.ParserError('host', addr + ': A name is required when providing MAC or comment')
        net_dict = self.state_dict['networks'][self.current_net]
        if addr in net_dict:
            raise errors.ParserError('host', addr + ': This host is already defined')
        addr_obj = ipaddress.ip_address(addr)
        if addr_obj not in self.current_net_obj:
            err_msg = addr + ': This host does not belong in the current network ('+self.current_net+')'
            raise errors.ParserError('host', err_msg)
        net_dict[addr] = {}
        if name is not None:
            net_dict[addr]['name'] = name
        if mac is not None:
            net_dict[addr]['mac'] = mac
        if comment is not None:
            net_dict[addr]['comment'] = comment
        self.current_ip = addr
        self.current_ip_obj = addr_obj

    def alias(self, alias=None, comment=None):
        if alias is None:
            raise errors.ParserError('alias', 'No alias provided')
        self.__require_unique_name('alias', alias)
        self.__require_ip('alias', alias)
        ip_dict = self.state_dict['networks'][self.current_net][self.current_ip]
        if 'cnames' not in ip_dict:
            ip_dict['cnames'] = []
        cname_dict = {'cname': alias}
        if comment is not None:
            cname_dict['comment'] = comment
        ip_dict['cnames'].append(cname_dict)

    def cname(self, alias=None, canonical=None, comment=None):
        if alias is None:
            raise errors.ParserError('cname', 'No alias provided')
        if canonical is None:
            raise errors.ParserError('alias', 'No canonical name provided')
        self.__require_unique_name('cname', alias)
        if 'cnames' not in self.state_dict:
            self.state_dict['cnames'] = {}
        cname_dict = {'canonical': canonical}
        if comment is not None:
            cname_dict['comment'] = comment
        self.state_dict['cnames'][alias] = cname_dict

#import pprint
#pprint.pprint(parse('./testdata', '#'))
