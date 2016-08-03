import os
from subprocess import Popen, PIPE
from dockermaster.main import USAGE
from contextlib import contextmanager

DIR = os.path.dirname(os.path.abspath(__file__))
APP1 = os.path.join(DIR, 'app1')

@contextmanager
def chdir(path):
    pwd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(pwd)

#-------------------------------------------------------------------------------

def test_invocation():
    p = Popen('docker-master', stdout=PIPE, shell=True)
    out = p.communicate()[0].decode('utf-8') 
    assert out == USAGE + '\n'
    assert p.returncode == 1

    with chdir(APP1):
        p = Popen('docker-master validate', stdout=PIPE, shell=True)
        out = p.communicate()[0].decode('utf-8')
        lines = out.strip().split('\n')
        assert lines[-1] == 'Validation successful'
        assert p.returncode == 0

#-------------------------------------------------------------------------------
