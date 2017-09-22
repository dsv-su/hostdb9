# coding=utf-8

import requests, json, copy, sys
import errors

class Client:
    def __init__(self, conf, warn):
        url = conf['baseurl']
        if not url.endswith('/'):
            url += '/'
        self.baseurl = url
        self.session = requests.Session()
        self.session.auth = (conf['user'], conf['password'])
        self.session.verify = bool(conf['verify_ssl'])
        self.warn = warn

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
                return self.do_request('get', path, **kwargs)
            except errors.IpamError as e:
                if e.message['code'] == 'Client.Ibap.Proto':
                    return self.get(path, paginate=1, **kwargs)
                else:
                    raise e

    def __get_first_page(self, path, **kwargs):
        if not kwargs:
            kwargs = {'params': {}}
        if '_paging' not in kwargs['params']:
            params = kwargs['params']
            params['_paging'] = 1
            params['_max_results'] = 500
            params['_return_as_object'] = 1
        return self.do_request('get',
                               path,
                               **kwargs)

    def __get_next_page(self, path, page):
        return self.do_request('get',
                               path,
                               params={'_page_id': page})

    def do_request(self, method, path, **kwargs):
        r = self.session.request(method,
                                 self.baseurl + path,
                                 **kwargs)
        j = r.json()
        if r.ok:
            return j
        else:
            raise errors.IpamError(r.status_code, j)

    def __get_ref(self, path, name=None, params=None):
        if not params:
            params = {}
        if name is not None:
            params['name'] = name
        remote_obj = self.get(path, params=params)
        if len(remote_obj) > 1:
            raise errors.ClientError("Ambiguous result: " + json.dumps(remote_obj))
        if len(remote_obj) == 0:
            raise errors.ClientError("Ref not found: " + path + ' ' + name)
        return remote_obj[0]['_ref']

    def restart_dhcp(self):
        data = {'_function': 'requestrestartservices',
                'mode': 'SEQUENTIAL',
                'services': 'DHCP'}
        self.get(self.__get_ref('grid'), data=json.dumps(data))

    def search(self, terms_dict):
        return self.get('allrecords',
                        paginate=1,
                        params=terms_dict)

    def list_vlans(self):
        return self.get('network',
                        params={'_return_fields': 'network,comment'})

    def list_vlan_ips(self, vlan_cidr):
        return self.get('ipv4address', params={'network': vlan_cidr})

    def list_cnames(self):
        return self.get('record:cname')

    def get_host_info(self, host):
        result = self.get(self.__get_ref('record:host', host), params={'_return_fields': 'comment,aliases'})
        comment = ''
        aliases = []
        if 'comment' in result:
            comment = result['comment']
        if 'aliases' in result:
            aliases = result['aliases']
        return (comment, aliases)

    def execute(self, changes):
        methods = {'create': 'post',
                   'update': 'put',
                   'delete': 'delete'}
        needrestart = False
        for change in changes:
            action = change['action']
            rtype  = change['type']
            data   = change['data']
            if action != 'create':
                if rtype == 'record:host':
                    rtype = self.__get_ref(rtype, name=change['olddata']['name'])
                else:
                    rtype = self.__get_ref(rtype, params=json.dumps(data))
            if action == 'delete':
                self.do_request(methods[action], rtype)
            else:
                self.do_request(methods[action], rtype, data=json.dumps(data))

    def diff(self, base, target):
        (host_add, host_update, host_remove) = self.__diff_hosts(copy.deepcopy(base['hosts']),
                                                                    copy.deepcopy(target['hosts']))
        (range_add, range_remove) = self.__diff_ranges(copy.deepcopy(base['ranges']),
                                                       copy.deepcopy(target['ranges']))
        (cname_add, cname_remove) = self.__diff_cnames(copy.deepcopy(base['cnames']),
                                                       copy.deepcopy(target['cnames']))
        actions = []
        lists = (cname_remove, host_remove, range_remove, host_update, host_add, cname_add, range_add)
        for action in lists:
            actions.extend(action)
        return actions

    def __diff_hosts(self, base, target):
        additions = []
        updates = []
        removals = []
        for network, ips in target.items():
            if network not in base:
                if self.warn:
                    print("Warning! Nonexistent network: "+ network)
                continue
            for ip, data in ips.items():
                if ip not in base[network]:
                    additions.append(self.__def_host('create', ip, data))
                else:
                    olddata = base[network][ip]
                    if data != olddata:
                        if olddata == {}:
                            additions.append(self.__def_host('create', ip, data))
                        else:
                            updates.append(self.__def_host('update', ip, data, olddata))
                    base[network].pop(ip)
        for network, ips in base.items():
            if network not in target:
                if self.warn:
                    print("Ignoring network: "+ network)
                continue
            for ip, data in ips.items():
                if data:
                    removals.append(self.__def_host('delete', ip, data))
        return (additions, updates, removals)

    def __diff_ranges(self, base, target):
        additions = []
        removals = []
        for network, ranges in target.items():
            if network not in base:
                continue
            for dhrange in ranges:
                if dhrange not in base[network]:
                    additions.append(self.__def_range('create', dhrange))
                else:
                    base[network].remove(dhrange)
        for network, ranges in base.items():
            if network not in target:
                continue
            for dhrange in ranges:
                removals.append(self.__def_range('delete', dhrange))
        return (additions, removals)

    def __diff_cnames(self, base, target):
        additions = []
        removals = []
        for canonical, aliases in target.items():
            for alias in aliases:
                if canonical not in base or alias not in base[canonical]:
                    additions.append(self.__def_cname('create', alias, canonical))
                else:
                    base[canonical].remove(alias)
        for canonical, aliases in base.items():
            for alias in aliases:
                removals.append(self.__def_cname('delete', alias, canonical))
        return (additions, removals)

    def __def_host(self, action, ip, data, olddata=None):
        ipdata = {'ipv4addr': ip}
        if 'mac' in data:
            ipdata['mac'] = data['mac']
        result = {'action': action,
                  'type': 'record:host',
                  'data': {'name': data['name'],
                           'ipv4addrs': [ipdata],
                           'comment': ''}}
        if olddata is not None:
            result['olddata'] = olddata
        for key in ('comment', 'aliases'):
            if key in data:
                result['data'][key] = data[key]
        return result

    def __def_range(self, action, dhrange):
        (start, end) = dhrange
        return {'action': action,
                'type': 'range',
                'data': {'start_addr': start,
                         'end_addr': end,
                         'server_association_type': 'FAILOVER',
                         'failover_association': 'ib-prod-dhcp'}}

    def __def_cname(self, action, alias, canonical):
        return {'action': action,
                'type': 'record:cname',
                'data': {'name': alias,
                         'canonical': canonical}}


