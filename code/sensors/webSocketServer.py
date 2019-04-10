from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

import sys, time, json
from twisted.python import log
from twisted.internet import task, reactor
from twisted.internet.defer import Deferred

'''
import dataCollectionPieces as dataShards
try:
    dataShards.setup()
except Exception as e:
    print(e)
    sys.exit(1)
else:
    print('Successful Gyroscope Startup')
'''

# then use getDataFragment()

# !!! important !!! <- the serial connection must be set up BEFORE the twisted stuff 
# because upon hitting an error it must shutdown the program and should not be ingored or silenced
# if handled it must call sys.exit or something else to terminate the program

i = 0
def pseudoGetDataFragment():
    global i

    i += 10
    t = time.localtime()
    t = ':'.join([str(i).zfill(2) for i in [t.tm_hour, t.tm_min, t.tm_sec]])

    return [t, i, i, i, i, i, i, i, i, i, i]
    # [t, externalTemp, coreTemp, round(internalTemp, 2), \
    #                  round(heading, 2), round(roll, 2), round(pitch, 2), \
    #                  round(magField, 4), round(x, 3), round(y, 3), round(z, 3)]

# Fetch data every x seconds
timeout = 5.0 # in seconds

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
        if isBinary:
            print('Error: Should not get binary')
        else:
            print('Text message received: {0}'.format(msg.decode('utf8')))

        #msg = s.encode('utf8')
        self.sendMessage(msg, isBinary)

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
        msg = json.dumps(pseudoGetDataFragment())
        print("broadcasting message '{}' ..".format(msg))
        for c in self.clients:
            c.sendMessage(msg.encode('utf8'))
            print("message sent to {}".format(c.peer))

log.startLogging(sys.stdout) # replace with log file

server = ServerFactory(u'ws://127.0.0.1:5005') # update this!
server.protocol = ServerProtocol

reactor.listenTCP(5005, server)

time.sleep(abs(time.time() % -5)) # wait till the next whole 5 seconds
starttime = time.time()

l = task.LoopingCall(server.broadcast)
l.start(timeout)
reactor.run()
