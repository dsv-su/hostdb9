import requests

class Infoblox:
    def __init__(self, baseurl, user, password):
        self.baseurl = baseurl
        self.auth = (user, password)

    def req(self, method, path, **kwargs):
        return requests.request(method, self.baseurl + path, auth=self.auth, **kwargs)

    def get_names_from_subnet(self, subnet):
        pass
