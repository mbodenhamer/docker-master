from subprocess import Popen, PIPE

#-------------------------------------------------------------------------------

def test_invocation():
    p = Popen('docker-master', stdout=PIPE, shell=True)
    out = p.communicate()[0].decode('utf-8') 
    assert out == 'docker-master MODE [options] [arguments]\n\n'

#-------------------------------------------------------------------------------
