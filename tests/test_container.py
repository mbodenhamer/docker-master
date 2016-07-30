from dockermaster.main import Container

from docker import Client
cli = Client(base_url='unix://var/run/docker.sock')

#-------------------------------------------------------------------------------
# Container

def test_container():
    c = Container(name = 'test1')
    assert c.full_name == c.name == 'test1'

    c = Container(name = 'test1', context='con1')
    assert c.full_name == 'con1_test1'
    assert c.name == 'test1'

#-------------------------------------------------------------------------------
