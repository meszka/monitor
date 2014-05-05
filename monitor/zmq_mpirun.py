#!/usr/bin/env python3

import sys
import random
from subprocess import Popen

from monitor.zmq_hosts import host_for

size = int(sys.argv[1])
script = sys.argv[2]

portbase = random.randint(9000,10000)

ssh_options = ['-oStrictHostKeyChecking=no']

def cmd(rank):
    # return [sys.executable, script, str(i), str(size), str(portbase)]
    host = host_for(rank)
    directory = sys.path[0]
    return ['ssh'] + ssh_options + [host,
            '{0}/../env/bin/python {0}/{1} {2} {3} {4}'.format(
                directory, script, rank, size, portbase)]

# ps = [Popen(cmd(i)) for i in range(size)]
ps = []
for i in range(size):
    print(cmd(i))
    ps.append(Popen(cmd(i)))

try:
    for p in ps:
        p.wait()
except KeyboardInterrupt:
    for p in ps:
        print('terminating', p)
        p.terminate()
