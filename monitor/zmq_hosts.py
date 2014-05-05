try:
    with open('hosts.txt') as f:
        hosts = f.read().splitlines()
except:
    hosts = []

if not hosts:
    hosts = ['localhost']

def host_for(rank):
    return hosts[rank % len(hosts)]
