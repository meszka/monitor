#!/usr/bin/env python3

import sys
import random
from subprocess import Popen

size = int(sys.argv[1])
script = sys.argv[2]

portbase = random.randint(9000,10000)

def cmd(i):
    return [sys.executable, script, str(i), str(size), str(portbase)]

ps = [Popen(cmd(i)) for i in range(size)]

for p in ps:
    p.wait()
