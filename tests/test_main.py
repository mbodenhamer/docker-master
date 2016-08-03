import os
from shlex import shlex
from dockermaster.main import _main

from docker import Client
cli = Client(base_url='unix://var/run/docker.sock')

DIR = os.path.dirname(os.path.abspath(__file__))
APP1 = os.path.join(DIR, 'app1')

#-------------------------------------------------------------------------------
# App1

def test_main_app1():
    def invoke(cmd):
        _main(*shlex(cmd))

    os.chdir(APP1)
    invoke('setup')
    invoke('up')
    invoke('stop')
    invoke('start')
    invoke('restart')
    invoke('run sa')
    invoke('status')
    invoke('shell simple pwd')
    invoke('bash simple pwd')
    invoke('pause sa')
    invoke('unpause sa')
    invoke('stop sa')
    invoke('start sa')
    invoke('restart sa')
    invoke('down')
    invoke('rmi')

#-------------------------------------------------------------------------------
