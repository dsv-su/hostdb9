# coding=utf-8
import requests, json

class Infoblox:
    def __init__(self, conf):
        baseurl = conf['baseurl']
        if not baseurl.endswith('/'):
            baseurl += '/'
        self.baseurl = baseurl
        self.session = requests.Session()
        self.session.auth = (conf['user'], conf['password'])

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

    def __next_available_ip(self, vlan_ref):
        result = self.post(vlan_ref, 
                           data='{"num":1}', 
                           params={'_function': 'next_available_ip'})
        return result['ips'][0]

    def __get_ref(self, rtype, name):
        remote_obj = self.get(rtype, params={'name': name})
        if len(remote_obj) > 1:
            raise ClientError("Ambiguous result: " + json.dumps(remote_obj))
        if len(remote_obj) == 0:
            raise ClientError("Hostname not found: " + host)
        return remote_obj[0]['_ref']

    def search(self, terms_dict):
        return self.get('allrecords', 
                        paginate=1,
                        params=terms_dict)

    def list_vlans(self):
        return self.get('network',
                        params={'_return_fields': 'network,comment'})

    def list_vlan_ips(self, vlan_cidr):
        return self.get('ipv4address', params={'network': vlan_cidr})

    def list_cnames(self, tld):
        return self.get('record:cname', params={'name~': tld})

    def create_host_auto(self, vlan_cidr, host, mac=None):
        vlans = self.list_vlans()
        vlan_ref = None
        for vlan in vlans:
            if vlan['network'] == vlan_cidr:
                vlan_ref = vlan['_ref']
                break
        if vlan_ref is None:
            raise ClientError("Network not found: " + vlan_cidr)
        ip = self.__next_available_ip(vlan_ref)
        return self.create_host(ip, host, mac)

    def create_host(self, ip, host, mac=None):
        data = {'name': host,
                'ipv4addrs': [{'ipv4addr': ip}]}
        if mac is not None:
            data['ipv4addrs'][0]['mac'] = mac
        return self.post('record:host', data=json.dumps(data))

    def delete_host(self, host):
        return self.delete(self.__get_ref('record:host', host))

    def create_alias(self, host, alias):
        data = {'name': alias,
                'canonical': host}
        return self.post('record:cname', data=json.dumps(data))

    def delete_alias(self, alias):
        return self.delete(self.__get_ref('record:cname', alias))

class ClientError(Exception):
    def __init__(self, message):
        self.message = message

class IpamError(Exception):
    def __init__(self, result, response):
        self.result = result
        self.response = response
