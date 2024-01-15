#!/usr/bin/env python3
import resource
import os
import random
import time
import threading
import socket
import signal
import struct

# runsettings
NUM_CONNECTIONS = 56511
# NUM_CONNECTIONS = 11
RANDOM_WINDOW_SIZE = 1000
ENABLE_RANDOM_OFFSET = False
RNG_SEED = 1

SRC_IP = "127.9.9.1"
DEST_IP = "127.9.9.2"
DEST_PORT = 9999
IP_BIND_ADDRESS_NO_PORT = 24
IP_LOCAL_PORT_RANGE	= 51
MAX_PORT = (2**16) - 1
MIN_PORT = MAX_PORT - 56511

class ServerState:
    canceled = False
    started = False
    thread = None
serverState = ServerState()

def server():
    connections = []
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.setblocking(False)
    sk.bind((DEST_IP, DEST_PORT))
    sk.listen()
    serverState.started = True
    print("server: started on {}:{}".format(DEST_IP, DEST_PORT))
    while not serverState.canceled:
        try:
            conn, addr = sk.accept()
            connections.append(conn)
        except:
            pass

    print("server: closing {} connections".format(len(connections)))
    for c in connections:
        c.close()
    
    sk.close()
    print("server: server closed")

def progClosed(arg1, arg2):
    serverState.canceled = True
    serverState.thread.join()

def getPortRange():
    return (MIN_PORT, MAX_PORT, MAX_PORT - MIN_PORT)

def randomizePortRangeOffset(portRange):
    (min, max, range) = portRange
    newRange = RANDOM_WINDOW_SIZE
    offset = random.randint(min, max - newRange)
    t = (offset, offset + newRange, newRange)
    return t if ENABLE_RANDOM_OFFSET else portRange

def packPortRange(portRange):
    (min, max, range) = portRange
    range = (max << 16) | min
    bytes = struct.pack("@I", range)
    return bytes

def makeConnections(dataFileName):
    connections = []
    dataFile = open(dataFileName, 'w+')

    for i in range(0, NUM_CONNECTIONS):
        errored = False
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.setsockopt(socket.IPPROTO_IP, IP_BIND_ADDRESS_NO_PORT, 1)
        sk.setsockopt(socket.IPPROTO_IP, IP_LOCAL_PORT_RANGE, 
            packPortRange(randomizePortRangeOffset(getPortRange())))
        sk.bind((SRC_IP, 0))
        startTime = 0
        endTime = 0
        try:
            startTime = time.time()
            sk.connect((DEST_IP, DEST_PORT))
            endTime = time.time()
            connections.append(sk)
        except Exception as e:
            endTime = time.time()
            errored = True

        port = sk.getsockname()[1] if not errored else -1
        dataFile.write("{},{}\n".format(
            port,
            endTime - startTime,
        ))

    dataFile.close()

def main():
    global serverState
    random.seed(RNG_SEED)
    (softRLimit, hardRLimit) = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (hardRLimit, hardRLimit))

    uname = os.uname()
    dataFileName = "{}-{}.csv".format(
        int(time.time()),
        uname.release)
    
    signal.signal(signal.SIGINT, progClosed)

    print("expected connections: {} min port: {} max port: {}".format(
        NUM_CONNECTIONS,
        MIN_PORT,
        MAX_PORT))
    print("filename: {}".format(dataFileName))

    serverState.thread = threading.Thread(target=server)
    serverState.thread.start()

    while not serverState.started:
        pass

    makeConnections(dataFileName)
    
    serverState.canceled = True
    serverState.thread.join()

if __name__ == "__main__":
    main()
