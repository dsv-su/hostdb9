# coding=utf-8

import requests, json
import errors

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
            except errors.IpamError as e:
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
            raise errors.IpamError(r.status_code, j)

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

