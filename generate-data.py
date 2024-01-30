#!/usr/bin/env python3
import random
import time
import threading
import socket
import signal
import struct
import argparse

SRC_IP = "127.9.9.1"
DEST_IP = "127.9.9.2"
DEST_PORT = 999
IP_BIND_ADDRESS_NO_PORT = 24
IP_LOCAL_PORT_RANGE	= 51

class ServerState:
    canceled = False
    started = False
    thread = None
serverState = ServerState()

class ConnectState:
    min_port = 0
    max_port = 0
    random_offset_window = 0

    def connections(self):
        return self.max_port - self.min_port + 1

connectState = ConnectState()

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
    exit(0)

def getPortRange():
    global connectState
    return (connectState.min_port, connectState.max_port, connectState.connections())

def randomizePortRangeOffset(portRange):
    global connectState
    if connectState.random_offset_window <= 0:
        return portRange
    (min, max, range) = portRange
    newRange = connectState.random_offset_window
    offset = random.randint(min, max - newRange)
    t = (offset, offset + newRange, newRange)
    return t

def packPortRange(portRange):
    (min, max, range) = portRange
    range = (max << 16) | min
    bytes = struct.pack("@I", range)
    return bytes

def makeConnections(dataFileName):
    global connectState
    connections = []
    dataFile = open(dataFileName, 'w+')

    for i in range(0, connectState.connections()):
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
    global connectState

    parser = argparse.ArgumentParser(description='Generates a .csv of data points')
    parser.add_argument('--random_offset_window',type=int,help='when specified enables the feature. this sets the window size')
    parser.add_argument('port_range', help='min,max ex. 9024,65535')
    parser.add_argument('data_filename')
    args = parser.parse_args()
    print(args)
    
    (rmin,rmax) = args.port_range.split(',')
    connectState.min_port = int(rmin)
    connectState.max_port = int(rmax)
    connectState.random_offset_window = int(args.random_offset_window)

    dataFileName = "{}.csv".format(args.data_filename)
    
    signal.signal(signal.SIGINT, progClosed)

    print("expected connections: {} min port: {} max port: {}".format(
        connectState.connections(),
        connectState.min_port,
        connectState.max_port))
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
