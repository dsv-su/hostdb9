import requests, json

class Infoblox:
    def __init__(self, baseurl, user, password):
        if not baseurl.endswith('/'):
            baseurl += '/'

        self.session = requests.Session()
        self.session.auth = (user, password)
        self.baseurl = baseurl

    def get(self, path, **kwargs):
        r = self.__get_first_page(path, **kwargs)
        out = list()
        while 'next_page_id' in r:
            out.extend(r['result'])
            r = self.__get_next_page(path, r['next_page_id'])
        out.extend(r['result'])
        return out

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

    def __do_request(self, method, path, **kwargs):
        r = self.session.request(method,
                                 self.baseurl + path,
                                 **kwargs)
        j = r.json()
        if r.ok:
            return j
        else:
            raise IpamError(r.status_code, j)

    def search(self, terms_dict):
        return self.get('allrecords',
                        params=terms_dict)

    def list_vlans(self):
        return self.get('network',
                        params={'_return_fields': 'network,comment'})

    def list_vlan_hosts(self, vlan):
        pass

    def create_host_auto(self, vlan, host, mac=None):
        pass

    def create_host(self, ip, host, mac=None):
        pass

    def delete_host(self, host):
        pass

    def create_alias(self, host, alias):
        pass

    def delete_alias(self, alias):
        pass

    def create_record(self, rtype, name, value):
        pass

    def delete_record(self, rtype, name):
        pass

class IpamError(Exception):
    def __init__(self, result, response):
        self.result = result
        self.response = response
