# coding=utf-8

import ipaddress
import errors

class Parser(object):
    def __init__(self, default_suffix):
        if not default_suffix.startswith('.'):
            default_suffix = '.' + default_suffix
        self.default_suffix = default_suffix
        self.comment_string = '#'
        self.reserved_names = ['dhcp', 'reserved', 'ledig']
        self.current_net = None
        self.current_net_obj = None
        self.current_ip = None
        self.prev_ip = None
        self.current_cname = None
        self.context = 'none'
        self.dhcp_start = None
        self.dhcp_end = None
        self.clear_state()

    def parse(self, dns_iterable):
        for line in dns_iterable:
            line = line.split(self.comment_string, maxsplit=1)[0].strip()
            if len(line) == 0:
                continue
            parts = line.split(maxsplit=1)
            try:
                handler = getattr(self, 'parse_' + parts[0])
                handler(*parts[1:])
            except AttributeError as e:
                raise errors.ParserError('directive', 'Invalid directive: ' + parts[0])
        self.__cleanup()
        return self.state_dict

    def get_state(self):
        return self.state_dict

    def clear_state(self):
        self.state_dict = {'hosts': {},
                           'ranges': {},
                           'cnames': {}}

    def __cleanup(self):
        if self.dhcp_start is not None:
            self.__add_range(self.dhcp_start, self.prev_ip)

    def __require_context(self, caller, req_context, data):
        if self.context != req_context:
            err_msg = data + ': Current context is ' + self.context + ', but ' + req_context + ' required'
            raise errors.ParserError(caller, err_msg)

    def __require_net(self, caller, data):
        if self.current_net_obj is None:
            raise errors.ParserError(caller, data + ': Unable to determine network parent')
        return self.state_dict['hosts'][self.current_net]

    def __require_ip(self, caller, data):
        self.__require_net(caller, data)
        if self.current_ip is None:
            raise errors.ParserError(caller, data + ': Unable to determine ip address parent')
        return self.state_dict['hosts'][self.current_net][self.current_ip]

    def __require_unique_name(self, caller, name):
        for category, content in self.state_dict.items():
            if category == 'cnames':
                for cname in content:
                    if cname == name:
                        canonical = content[cname]['canonical']
                        err_msg = name + ': This name is already an alias for ' + canonical
                        raise errors.ParserError(caller, err_msg)
            elif category == 'hosts':
                for network, hosts in content.items():
                    for addr, data in hosts.items():
                        if 'name' in data and data['name'] == name:
                            err_msg = name + ': This name is already a canonical name'
                            raise errors.ParserError(caller, err_msg)
                        if 'aliases' in data:
                            for addr_alias in data['aliases']:
                                if addr_alias == name:
                                    err_msg = name + ': This name is already an alias for ' + data['name']
                                    raise errors.ParserError(caller, err_msg)

    def __expand_name(self, name, addr=None):
        if name in self.reserved_names:
            if addr is not None:
                name = name + '-' + addr.replace('.', '-')
            else:
                raise errors.ParserError('name expansion', name + ' is expandable but no address was provided')
        if '.' not in name:
            name = name + self.default_suffix
        return name

    def __add_range(self, start, end):
        ranges = self.state_dict['ranges'][self.current_net]
        ranges.append((start, end))
        self.dhcp_start = None

    def parse_network(self, cidr=None):
        if cidr is None:
            raise errors.ParserError('network', 'No network address provided')
        net_dict = self.state_dict['hosts']
        if cidr in net_dict:
            raise errors.ParserError('network', cidr + ': This network is already defined')
        net_dict[cidr] = {}
        self.state_dict['ranges'][cidr] = []
        self.current_net = cidr
        self.current_net_obj = ipaddress.ip_network(cidr)
        self.current_ip = None
        self.prev_ip = None
        self.current_cname = None
        self.dhcp_start = None
        self.context = 'network'

    def parse_host(self, addr=None):
        if addr is None:
            raise errors.ParserError('host', 'No host address provided')
        net_dict = self.__require_net('host', addr)
        if addr in net_dict:
            raise errors.ParserError('host', addr + ': This host is already defined')
        addr_obj = ipaddress.ip_address(addr)
        if addr_obj not in self.current_net_obj:
            err_msg = addr + ': This host does not belong in the current network ('+self.current_net+')'
            raise errors.ParserError('host', err_msg)
        net_dict[addr] = {}
        self.prev_ip = self.current_ip
        self.current_ip = addr
        self.context = 'host'

    def parse_name(self, name=None):
        self.__require_context('name', 'host', name)
        if name is None:
            raise errors.ParserError('name', 'No host name provided')
        ip_dict = self.__require_ip('name', name)
        name = self.__expand_name(name, self.current_ip)
        if name.startswith('dhcp') and self.dhcp_start is None:
            self.dhcp_start = self.current_ip
        elif not name.startswith('dhcp') and self.dhcp_start is not None:
            self.__add_range(self.dhcp_start, self.prev_ip)
        self.__require_unique_name('name', name)
        if 'name' in ip_dict:
            raise errors.ParserError('name', name + ': ' + self.current_ip + ' already has a name')
        ip_dict['name'] = name

    def parse_mac(self, mac=None):
        self.__require_context('mac', 'host', mac)
        if mac is None:
            raise errors.ParserError('mac', 'No mac address provided')
        ip_dict = self.__require_ip('mac', mac)
        if 'name' not in ip_dict:
            err_msg = self.current_ip + ': Hostname must be specified before mac address'
            raise errors.ParserError('mac', err_msg)
        if ip_dict['name'].startswith('dhcp'):
            err_msg = self.current_ip + ': DHCP hosts cannot have a static mac address assigned'
            raise errors.ParserError('mac', err_msg)
        if 'mac' in ip_dict:
            err_msg = self.current_ip + ': There is already a mac address for this host'
            raise errors.ParserError('mac', err_msg)
        ip_dict['mac'] = mac.upper()

    def parse_comment(self, comment):
        self.__require_context('comment', 'host', comment)
        if comment is None:
            raise errors.ParserError('comment', 'No comment provided')
        ip_dict = self.__require_ip('comment', comment)
        if 'comment' in ip_dict:
            raise errors.ParserError('comment', self.current_ip + ': There is already a comment for this host')
        ip_dict['comment'] = comment

    def parse_alias(self, alias=None):
        self.__require_context('alias', 'host', alias)
        if alias is None:
            raise errors.ParserError('alias', 'No alias provided')
        alias = self.__expand_name(alias, self.current_ip)
        self.__require_unique_name('alias', alias)
        ip_dict = self.__require_ip('alias', alias)
        if 'name' not in ip_dict:
            raise errors.ParserError('alias', alias + ': There is no canonical name for this alias')
        if 'aliases' not in ip_dict:
            ip_dict['aliases'] = []
        ip_dict['aliases'].append(alias)

    def parse_cname(self, alias=None):
        if alias is None:
            raise errors.ParserError('cname', 'No alias provided')
        alias = self.__expand_name(alias, None)
        self.__require_unique_name('cname', alias)
        self.current_cname = alias
        self.context = 'cname'

    def parse_target(self, target=None):
        self.__require_context('target', 'cname', target)
        if target is None:
            raise errors.ParserError('target', 'No target provided')
        target = self.__expand_name(target, None)
        cname_dict = self.state_dict['cnames']
        if target not in cname_dict:
            cname_dict[target] = []
        cname_dict[target].append(self.current_cname)
        self.current_cname = None
        self.context = 'none'

