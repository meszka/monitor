import os
import sys

try:
    with open(os.path.join(sys.path[0], 'hosts.txt')) as f:
        hosts = f.read().splitlines()
except:
    hosts = []

if not hosts:
    hosts = ['localhost']

def host_for(rank):
    return hosts[rank % len(hosts)]
