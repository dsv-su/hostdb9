# coding=utf-8

import json
import infoblox, errors

class Client:
    def __init__(self, conf):
        self.iblox = infoblox.Infoblox(conf['baseurl'],
                                       conf['user'],
                                       conf['password'],
                                       bool(conf['verify_ssl']))

    def __get_ref(self, path, name=None, params={}):
        if name is not None:
            params['name'] = name
        remote_obj = self.iblox.get(path, params=params)
        if len(remote_obj) > 1:
            raise errors.ClientError("Ambiguous result: " + json.dumps(remote_obj))
        if len(remote_obj) == 0:
            raise errors.ClientError("Ref not found: " + path + ' ' + name)
        return remote_obj[0]['_ref']

    def __next_available_ip(self, vlan_ref):
        result = self.iblox.post(vlan_ref,
                                 data='{"num":1}',
                                 params={'_function': 'next_available_ip'})
        return result['ips'][0]

    def __restart_dhcp(self):
        gridref = self.__get_ref('grid')
        data = {'_function': 'requestrestartservices',
                'mode': 'SEQUENTIAL',
                'services': 'DHCP'}
        self.iblox.get(gridref, data=json.dumps(data))

    def search(self, terms_dict):
        return self.iblox.get('allrecords',
                              paginate=1,
                              params=terms_dict)

    def list_vlans(self):
        return self.iblox.get('network',
                              params={'_return_fields': 'network,comment'})

    def list_vlan_ips(self, vlan_cidr):
        return self.iblox.get('ipv4address', params={'network': vlan_cidr})

    def list_cnames(self, host):
        return self.iblox.get('record:cname', params={'canonical': host})

    def list_iblox_aliases(self, host):
        result = self.iblox.get('record:host', params={'name': host,
                                                       '_return_fields': 'aliases'})
        if len(result) != 1:
            raise errors.ClientError("Ambiguous result: " + json.dumps(result))
        return result[0]['aliases']

    def list_dhcp_ranges(self, vlan_cidr):
        return self.iblox.get('range', params={'network': vlan_cidr})

    def create_host_auto(self, vlan_cidr, host, mac=None):
        vlan = self.iblox.get('network',
                              params={'network': vlan_cidr})
        if len(vlan) > 1:
            raise errors.ClientError("Ambiguous result: " + vlan)
        vlan = vlan[0]
        if '_ref' not in vlan:
            raise errors.ClientError("Network not found: " + vlan_cidr)
        ip = self.__next_available_ip(vlan['_ref'])
        return self.create_host(ip, host, mac)

    def create_host(self, ip, host, mac=None):
        data = {'name': host,
                'ipv4addrs': [{'ipv4addr': ip}]}
        if mac is not None:
            data['ipv4addrs'][0]['mac'] = mac
        ref = self.iblox.post('record:host', data=json.dumps(data))
        if mac is not None:
            self.__restart_dhcp()
        return ref

    def delete_host(self, host):
        return self.iblox.delete(self.__get_ref('record:host', host))

    def create_cname(self, host, alias):
        data = {'name': alias,
                'canonical': host}
        return self.iblox.post('record:cname', data=json.dumps(data))

    def delete_cname(self, alias):
        return self.iblox.delete(self.__get_ref('record:cname', alias))

    def create_dhcp_range(self, start, end, comment=None):
        data = {'start_addr': start,
                'end_addr': end,
                'server_association_type': 'FAILOVER',
                'failover_association': 'ib-prod-dhcp'}
        if comment is not None:
            data['comment'] = comment
        ref = self.iblox.post('range', data=json.dumps(data))
        self.__restart_dhcp()
        return ref

    def delete_dhcp_range(self, start, end):
        ref = self.iblox.delete(self.__get_ref('range', params={'start_addr': start,
                                                                'end_addr': end}))
        self.__restart_dhcp()
        return ref
