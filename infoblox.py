import configparser
import requests

class Infoblox:
    def __init__(self, conffile):
        conf = configparser.ConfigParser()
        conf.read(conffile)
        conf = conf['main']
        
        self.baseurl = conf['baseurl']
        self.auth = (conf['user'], conf['password'])

    def do(self, resource):
        return requests.get(self.baseurl + resource, auth=self.auth)
