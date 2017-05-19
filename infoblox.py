import requests

class Infoblox:
    def __init__(self, baseurl, auth):
        self.baseurl = baseurl
        self.auth = auth

    def do(self, resource):
        return requests.get(self.baseurl + resource, auth=self.auth)
