# coding=utf-8

class ClientError(Exception):
    def __init__(self, message):
        self.message = message

class IpamError(ClientError):
    def __init__(self, result, message):
        self.result = result
        self.message = message

class ParserError(ClientError):
    def __init__(self, context, message):
        self.context = context
        self.message = message
