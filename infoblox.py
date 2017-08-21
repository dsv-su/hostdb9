# coding=utf-8
import requests, json

class Infoblox:
    def __init__(self, url, username, password, verify_ssl):
        if url.endswith('/') is False:
            url += '/'
        self.baseurl = url
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = verify_ssl

    def get(self, path, paginate=0, **kwargs):
        if paginate == 1:
            r = self.__get_first_page(path, **kwargs)
            out = list()
            while 'next_page_id' in r:
                out.extend(r['result'])
                r = self.__get_next_page(path, r['next_page_id'])
                out.extend(r['result'])
            return out
        else:
            try:
                return self.__do_request('get', path, **kwargs)
            except IpamError as e:
                if e.response['code'] == 'Client.Ibap.Proto':
                    return self.get(path, paginate=1, **kwargs)
                else:
                    raise e

    def post(self, path, **kwargs):
        return self.__do_request('post', path, **kwargs)

    def put(self, ref, **kwargs):
        return self.__do_request('put', ref, **kwargs)

    def delete(self, ref, **kwargs):
        return self.__do_request('delete', ref, **kwargs)

    def __do_request(self, method, path, **kwargs):
        r = self.session.request(method,
                                 self.baseurl + path,
                                 **kwargs)
        j = r.json()
        if r.ok:
            return j
        else:
            raise IpamError(r.status_code, j)

    def __get_first_page(self, path, **kwargs):
        if not kwargs:
            kwargs = {'params': dict()}
        if '_paging' not in kwargs['params']:
            params = kwargs['params']
            params['_paging'] = 1
            params['_max_results'] = 500
            params['_return_as_object'] = 1
        return self.__do_request('get',
                                 path,
                                 **kwargs)

    def __get_next_page(self, path, page):
        return self.__do_request('get',
                                 path,
                                 params={'_page_id': page})

class Client:
    def __init__(self, iblox):
        self.iblox = iblox

    def __get_ref(self, path, name=None):
        params = {}
        if name is not None:
            params = {'name': name}
        remote_obj = self.iblox.get(path, params=params)
        if len(remote_obj) > 1:
            raise ClientError("Ambiguous result: " + json.dumps(remote_obj))
        if len(remote_obj) == 0:
            raise ClientError("Ref not found: " + path + ' ' + name)
        return remote_obj[0]['_ref']

    def __next_available_ip(self, vlan_ref):
        result = self.iblox.post(vlan_ref, 
                                 data='{"num":1}', 
                                 params={'_function': 'next_available_ip'})
        return result['ips'][0]

    def __restart_dhcp(self):
        gridref = self.__get_ref('grid')
        data = {'_function': 'requestrestartservicestatus',
                'member_order': 'SIMULTANEOUSLY',
                'service_option': 'DHCP'}
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
            raise ClientError("Ambiguous result: " + json.dumps(result))
        return result[0]['aliases']
        
    def list_dhcp_ranges(self, vlan_cidr):
        pass

    def create_host_auto(self, vlan_cidr, host, mac=None):
        vlan = self.iblox.get('network',
                              params={'network': vlan_cidr})
        if len(vlan) > 1:
            raise ClientError("Ambiguous result: " + vlan)
        vlan = vlan[0]
        if '_ref' not in vlan:
            raise ClientError("Network not found: " + vlan_cidr)
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

    def create_dhcp_range(self, start, end):
        pass

    def delete_dhcp_range(self, start, end):
        pass

class ClientError(Exception):
    def __init__(self, message):
        self.message = message

class IpamError(ClientError):
    def __init__(self, result, message):
        self.result = result
        self.message = message
