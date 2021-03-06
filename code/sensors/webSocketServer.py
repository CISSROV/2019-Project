#!/usr/bin/env python3.4
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory

import sys
import time
import json
import os
from twisted.python import log
from twisted.internet import task, reactor

# ---> NOTE <--- This process is - and must be - run and owned by root

import dataCollectShards as dataShards
try:
    dataShards.setup()
except Exception as e:
    print(e)
    sys.exit(1)
else:
    print('Successful Gyroscope Startup')

def getDateISO8601():
    tmp = time.localtime()
    return '{}-{:0>2}-{:0>2}'.format(tmp.tm_year, tmp.tm_mon, tmp.tm_mday)

IP = '127.0.0.1'
PORT = 5005

# then use getDataFragment()

# !!! important !!! <- the serial connection must be set up BEFORE the twisted stuff
# because upon hitting an error it must shutdown the program and should not be ingored or silenced
# if handled it must call sys.exit or something else to terminate the program

# Fetch data every x seconds
timeout = 1.0 # in seconds

class ServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        #print(request.path, request.protocols)
        print('Client connecting & registering: {0}'.format(request.peer))
        self.factory.register(self)

    def onOpen(self):
        print('WebSocket connection open')

    def onClose(self, wasClean, code, reason):
        print('WebSocket connection closed & unregistering: {0}'.format(reason))
        self.factory.unregister(self)

    def onMessage(self, msg, isBinary):
        if msg == b'hi':
            self.sendMessage(b'Hello World!')

class ServerFactory(WebSocketServerFactory):

    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.clients = []

    def register(self, client):
        if client not in self.clients:
            self.clients.append(client)

    def unregister(self, client):
        if client in self.clients:
            self.clients.remove(client)

    def broadcast(self):
        msg = json.dumps(dataShards.getDataFragment())
        print("broadcasting message '{}' ..".format(msg))
        for c in self.clients:
            c.sendMessage(msg.encode('utf8'))
            #print("message sent to {}".format(c.peer))

date = getDateISO8601()

try:
    f = open('/var/log/MATE/websocket{}.log'.format(date), 'a')
except FileNotFoundError:
    f = open('/var/log/MATE/websocket{}.log'.format(date), 'w')

log.startLogging(f) # replace with log file # sys.stdout

server = ServerFactory(u'ws://{}:{}'.format(IP , PORT)) # update this!
server.protocol = ServerProtocol

reactor.listenTCP(PORT, server)

time.sleep(abs(time.time() % -5)) # wait till the next whole 5 seconds
starttime = time.time()

l = task.LoopingCall(server.broadcast)
l.start(timeout)
try:
    reactor.run()
finally:
    f.close()
