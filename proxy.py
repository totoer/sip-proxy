#!/usr/bin/python3

import sys
import json
import copy
import socket
import logging
import argparse
from dataclasses import dataclass

from twisted.internet import reactor

from twisted.protocols import sip
from twisted.internet.protocol import ServerFactory


@dataclass
class Config:
    proxy_host: str
    proxy_port: int

    client_host: str
    client_port: int

    target_host: str
    target_port: int


class SipProxy(sip.Proxy):

    def __init__(self, config: Config, headers: dict):
        self._log = logging.getLogger('sip-proxy')
        self._log.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        self._log.addHandler(handler)

        self._config = config
        self._headers = headers
        super().__init__(host=config.proxy_host, port=config.proxy_port)
        self._log.info('Start')

    def handle_request(self, req: sip.Request, addr: tuple[str, int]):
        if addr == (self._config.target_host, self._config.target_port,):
            self._log.info('Handle request %s, target->client' % (req.method,))
            self.sendMessage(sip.URL(host=self._config.client_host,
                             port=self._config.client_port), req)

        else:
            self._log.info('Handle request %s, client->target' % (req.method,))

            bufferSpecialCases = copy.copy(sip.specialCases)
            headers = self._headers.get('request', {}).get(req.method, {})
            for k, v in headers.items():
                sip.specialCases[k.lower()] = k
                req.addHeader(k, v)
                self._log.info('Set header %s: %s, client->target' % (k, v,))

            self.sendMessage(sip.URL(host=self._config.target_host,
                             port=self._config.target_port), req)

            sip.specialCases = bufferSpecialCases

    def handle_response(self, resp: sip.Response, addr: tuple[str, int]):
        if addr == (self._config.target_host, self._config.target_port,):
            self._log.info('Handle response %s, target->client' % (resp.code,))
            self.deliverResponse(resp)
            self.sendMessage(sip.URL(host=self._config.client_host,
                             port=self._config.client_port), resp)

        else:
            self._log.info('Handle response %s, client->target' % (resp.code,))

            bufferSpecialCases = copy.copy(sip.specialCases)
            code = str(resp.code)
            headers = self._headers.get('response', {}).get(code, {})
            for k, v in headers.items():
                sip.specialCases[k.lower()] = k
                resp.addHeader(k, v)
                self._log.info('Set header %s: %s, client->target' % (k, v,))

            self.deliverResponse(resp)

            sip.specialCases = bufferSpecialCases


class sipfactory(ServerFactory):

    protocol = SipProxy


def main():
    parser = argparse.ArgumentParser(description='SIP proxy')
    parser.add_argument(
        '--proxy-host', help='Proxy host localhost:port ( or deafult port 5060 )', required=True)
    parser.add_argument(
        '--client-host', help='Client host localhost:port ( or deafult port 5060 )', required=True)
    parser.add_argument(
        '--target-host', help='Target host localhost:port ( or deafult port 5060 )', required=True)
    parser.add_argument('--headers', help='JSON file with headers')
    args = parser.parse_args()

    proxy_host_parts = args.proxy_host.split(':')
    proxy_port = int(proxy_host_parts[1]) if len(
        proxy_host_parts) == 2 else 5060

    client_host_parts = args.client_host.split(':')
    client_port = int(client_host_parts[1]) if len(
        client_host_parts) == 2 else 5060

    target_host_parts = args.target_host.split(':')
    target_port = int(target_host_parts[1]) if len(
        target_host_parts) == 2 else 5060

    proxy_host = socket.gethostbyname(proxy_host_parts[0])
    client_host = socket.gethostbyname(client_host_parts[0])
    target_host = socket.gethostbyname(target_host_parts[0])

    config = Config(proxy_host=proxy_host, proxy_port=proxy_port, client_host=client_host,
                    client_port=client_port, target_host=target_host, target_port=target_port)

    headers = {}
    if args.headers:
        with open(args.headers, 'r') as fp:
            headers = json.load(fp)

    p = SipProxy(config, headers)
    reactor.listenUDP(config.proxy_port, p, config.proxy_host)
    reactor.run()


if __name__ == '__main__':
    main()
