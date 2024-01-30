#!/usr/bin/env python3
import sys
import matplotlib.pyplot as plt
import csv

MS_IN_SECONDS = 1000

# ./plot-data.py < 1705358125-6.6.7-fred.csv > 1705358125-6.6.7-fred.png

class PortStats:
    TOTAL_LATENCY = 0
    TOTAL_PORTS = 0
    TOTAL_MIN_LATENCY = float('inf')
    TOTAL_MAX_LATENCY = 0
    GROUP_COLOR = {
        "even": "green",
        "odd": "red",
        "errored": "black"
    }
    
    def __init__(self, type):
        self.type = type
        self.latency = 0
        self.total = 0
        self.minLatency = float('inf')
        self.maxLatency = 0
        self.plot = []
    
    def addPort(self, latency):
        self.latency += latency
        self.plot.append((PortStats.TOTAL_PORTS, latency))
        PortStats.TOTAL_LATENCY += latency
        PortStats.TOTAL_PORTS += 1
        self.total += 1

        self.minLatency = latency if latency < self.minLatency else self.minLatency
        self.maxLatency = latency if latency > self.maxLatency else self.maxLatency
        
        PortStats.TOTAL_MIN_LATENCY = latency if latency < PortStats.TOTAL_MIN_LATENCY else PortStats.TOTAL_MIN_LATENCY
        PortStats.TOTAL_MAX_LATENCY = latency if latency > PortStats.TOTAL_MAX_LATENCY else PortStats.TOTAL_MAX_LATENCY
    
    def avgLatency(self):
        return self.latency / max(1, self.total)
    
    def __str__(self):
        return "{} ports: {} latency min: {}ms max: {}ms avg: {}ms".format(
            self.type,
            self.total,
            round(self.minLatency, 3),
            round(self.maxLatency, 3),
            round(self.avgLatency(), 3),
        )
    
    def color(self):
        return PortStats.GROUP_COLOR[self.type]
    
    def xAxis(self):
        return list(map(lambda p: p[0], self.plot))
    
    def yAxis(self):
        return list(map(lambda p: p[1], self.plot))
    
    def label(self):
        return "{} ports".format(self.type)

def main():
    evenPortStats = PortStats("even")
    oddPortStats = PortStats("odd")
    erroredPortStats = PortStats("errored")
    connections = 0

    for row in csv.reader(iter(sys.stdin.readline, '')):
        (port, latency) = row
        port = int(port)
        latency = float(latency) * MS_IN_SECONDS
        
        isErroredPort = port < 0
        isEvenPort = port % 2 == 0

        if isErroredPort:
            erroredPortStats.addPort(latency)
        else:
            if isEvenPort:
                evenPortStats.addPort(latency)
            else:
                oddPortStats.addPort(latency)

        connections += 1

    text = [
        "connection attempts: {} errored: {} total: {}".format(
            PortStats.TOTAL_PORTS,
            erroredPortStats.total,
            evenPortStats.total + oddPortStats.total
        ),
        "total time: {}s".format(round(PortStats.TOTAL_LATENCY / MS_IN_SECONDS, 3)),
        "latency: min: {}ms max: {}ms avg: {}ms".format(
            round(PortStats.TOTAL_MIN_LATENCY, 3), 
            round(PortStats.TOTAL_MAX_LATENCY, 3),
            round(PortStats.TOTAL_LATENCY / max(1, PortStats.TOTAL_PORTS), 3)
        ),
        str(evenPortStats),
        str(oddPortStats),
        str(erroredPortStats)
    ]

    # print("\n".join(text))

    fig, ax = plt.subplots()

    ax.set_title(label="\n".join(text), loc='left')
    
    ax.scatter(evenPortStats.xAxis(), evenPortStats.yAxis(), c=evenPortStats.color(), label=evenPortStats.label())
    ax.scatter(oddPortStats.xAxis(), oddPortStats.yAxis(), c=oddPortStats.color(), label=oddPortStats.label())
    ax.scatter(erroredPortStats.xAxis(), erroredPortStats.yAxis(), c=erroredPortStats.color(), label=erroredPortStats.label())
    # ax.axis([0, PortStats.TOTAL_PORTS, 0, 30])

    ax.set_yscale('log', base=2)
    ax.axis([0, PortStats.TOTAL_PORTS, PortStats.TOTAL_MIN_LATENCY, PortStats.TOTAL_MAX_LATENCY])
    
    ax.set_ylabel("Latency (ms)")
    ax.set_xlabel("Connection #")
    ax.legend(loc="upper left")

    fig.savefig(fname=sys.stdout, format="png", bbox_inches='tight')

if __name__ == "__main__":
    main()
