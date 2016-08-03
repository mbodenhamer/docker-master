import os
import sys
import time
import yaml
import socket
import docker

#-------------------------------------------------------------------------------

client = docker.Client(base_url='unix://var/run/docker.sock')

# Ignore the ugly monkeypatch...
# Will be removed in 0.1
if client._version > '1.21':
    client._version = '1.21'

#-------------------------------------------------------------------------------

def scan(addr, port):
    sock = socket.socket()
    try:
        sock.connect((addr, port))
        sock.close()
        return True
    except socket.error:
        pass
    return False

strbool = lambda s: s.lower() == 'yes' or s.lower() == 'true'

#-------------------------------------------------------------------------------


class Container(object):
    def __init__(self, **kwargs):
        for attr, val in kwargs.items():
            setattr(self, attr, val)

        self.name = getattr(self, 'name', '')
        if self.name:
            name = self.name
            context = getattr(self, 'context', '')
            if context:
                self.full_name = '{}_{}'.format(context, name)
            else:
                self.full_name = self.name
        else:
            self.full_name = self.name

        self.args = getattr(self, 'args', '')
        self.shell = getattr(self, 'shell', '/bin/bash')
        self.image = getattr(self, 'image', self.full_name)
        self.rootpath = getattr(self, 'rootpath', os.path.abspath(__file__))
        self.is_service = getattr(self, 'is_service', True)
        self.scan = list(map(int, getattr(self, 'scan', [])))
        self.expose = list(map(int, getattr(self, 'expose', [])))
        self.standalone = getattr(self, 'standalone', False)

        self.start_poll = getattr(self, 'start_poll', [])
        self.start_wait = getattr(self, 'start_wait', 0)

    @classmethod
    def from_dict(cls, dct, name, context='', rootpath=''):
        dct['name'] = name
        dct['context'] = context
        dct['rootpath'] = rootpath

        if 'start' in dct:
            start = dct['start']
            del dct['start']
            dct['start_order'] = start['order']
            dct['start_wait'] = start.get('wait', 0)
            dct['start_poll'] = start.get('poll', [])

        ret = Container(**dct)
        return ret

    def build_image(self):
        print('Building {}'.format(self.name))
        tag = self.full_name
        buildpath = os.path.join(self.rootpath, self.build)
        cmd = 'docker build -t {}:latest {}'.format(tag, buildpath)
        os.system(cmd)

    def pull_image(self):
        print('Pulling {}'.format(self.name))
        cmd = 'docker pull {}'.format(self.image)
        os.system(cmd)

    def runargs(self):
        volumes_from = getattr(self, 'argvolsfrom', 
                               getattr(self, 'volumes_from', []))
        volumes = getattr(self, 'argvols', getattr(self, 'volumes', []))
        ports = getattr(self, 'ports', [])
        links = getattr(self, 'arglinks', getattr(self, 'links', []))
        env = getattr(self, 'environment', {})
        command = getattr(self, 'command', '')
        restart = getattr(self, 'restart', '')
        expose = getattr(self, 'expose', [])

        ret = '--name {} '.format(self.full_name)
        if self.is_service:
            ret += '-d '

        if volumes_from:
            ret += ' '.join('--volumes-from {}'.format(c) for c in volumes_from)
            ret += ' '
        if volumes:
            ret += ' '.join('-v {}'.format(v) for v in volumes)
            ret += ' '
        if ports:
            ret += ' '.join('-p {}'.format(p) for p in ports)
            ret += ' '
        if links:
            ret += ' '.join('--link {}'.format(l) for l in links)
            ret += ' '
        if env:
            ret += ' '.join('-e {}="{}"'.format(k,v) for k,v in env.items())
            ret += ' '
        if restart:
            ret += '--restart ' + restart
            ret += ' '
        if expose:
            ret += ' '.join('--expose {}'.format(p) for p in expose)
            ret += ' '

        ret += self.image
        ret += ' ' + self.args
        if command:
            if isinstance(command, list):
                command = ' '.join(command)
            ret += ' ' + command
        return ret

    def _poll(self, cname, port):
        caddr = client.inspect_container(cname)['NetworkSettings']['IPAddress']

        sock = socket.socket()
        while True:
            try:
                sock.connect((caddr, port))
                sock.close()
                break
            except socket.error as e:
                if e.errno == 111:  # Connection refused
                    time.sleep(0.5)
                else:
                    raise e

    def poll(self):
        for poll in self.argpoll:
            cname, port = poll.split(':')
            self._poll(cname, int(port))

    def run(self):
        print("Running {}".format(self.name))
        if self.start_poll:
            self.poll()

        args = self.runargs()
        cmd = 'docker run {}'.format(args)
        print(cmd)
        os.system(cmd)
        if self.start_wait:
            time.sleep(self.start_wait)

    def start(self):
        print("Starting {}".format(self.name))
        if self.start_poll:
            self.poll()

        cmd = 'docker start {}'.format(self.full_name)
        os.system(cmd)
        if self.start_wait:
            time.sleep(self.start_wait)

    def stop(self):
        print("Stopping {}".format(self.name))
        cmd = 'docker stop {}'.format(self.full_name)
        os.system(cmd)

    def restart_container(self):
        print("Restarting {}".format(self.name))
        cmd = 'docker restart {}'.format(self.full_name)
        os.system(cmd)

    def pause(self):
        print("Pausing {}".format(self.name))
        cmd = 'docker pause {}'.format(self.full_name)
        os.system(cmd)

    def unpause(self):
        print("Unpausing {}".format(self.name))
        cmd = 'docker unpause {}'.format(self.full_name)
        os.system(cmd)

    def kill(self):
        print("Killing {}".format(self.name))
        cmd = 'docker kill {}'.format(self.full_name)
        os.system(cmd)

    def rm(self):
        print("Removing {}".format(self.name))
        cmd = 'docker rm -f -v {}'.format(self.full_name)
        os.system(cmd)

    def rmo(self):
        print("Removing {}".format(self.name))
        cmd = 'docker rm -f {}'.format(self.full_name)
        os.system(cmd)

    def rmi(self):
        print("rmi {}".format(self.image))
        cmd = 'docker rmi {}'.format(self.image)
        os.system(cmd)


#-------------------------------------------------------------------------------


class Application(object):
    def __init__(self, *args, **kwargs):
        self.containers = list(args)
        self.containers.sort(key=lambda x: getattr(x, 'start_order', 9999999))
        for attr, val in kwargs.items():
            setattr(self, attr, val)

        self.aliases = {c.name: c.full_name for c in self.containers}
        self.aliasmap = {c.name: c for c in self.containers}
        self.resolve_aliases()
        self.resolve_paths()

    @classmethod
    def from_yaml(cls, fil):
        dct = yaml.load(fil)
        name = dct.get('name', '')
        services = dct.get('services', {})
        root = os.path.dirname(os.path.abspath(fil.name))

        containers = []
        for key, val in services.items():
            c = Container.from_dict(val, key, context=name, rootpath=root)
            containers.append(c)

        ret = Application(*containers, name=name, rootpath=root)
        return ret

    def resolve_aliases(self):
        dct = self.aliases
        for c in self.containers:
            if hasattr(c, 'links'):
                arglinks = []
                for link in c.links:
                    src, dest = link.split(':')
                    newsrc = dct[src]
                    arglinks.append('{}:{}'.format(newsrc, dest))
                c.arglinks = arglinks
            
            if hasattr(c, 'start_poll'):
                argpoll = []
                for link in c.start_poll:
                    src, dest = link.split(':')
                    newsrc = dct[src]
                    argpoll.append('{}:{}'.format(newsrc, dest))
                c.argpoll = argpoll

            if hasattr(c, 'volumes_from'):
                argvolsfrom = []
                for src in c.volumes_from:
                    newsrc = dct[src]
                    argvolsfrom.append(newsrc)
                c.argvolsfrom = argvolsfrom

    def resolve_paths(self):
        for c in self.containers:
            if hasattr(c, 'volumes'):
                argvols = []
                for vol in c.volumes:
                    if ':' in vol:
                        splits = vol.split(':')
                        src = splits[0]
                        dest = ':'.join(splits[1:])
                        if src.startswith('./'):
                            srcname = src[2:]
                            newsrc = os.path.join(self.rootpath, srcname)
                            argvols.append('{}:{}'.format(newsrc, dest))
                        elif src.startswith('$app_env('):
                            var = self.name.upper() + '_' + src[9:-1]
                            if var in os.environ:
                                newsrc = os.environ[var]
                                if os.path.isdir(newsrc):
                                    argvols.append('{}:{}'.format(newsrc,dest))
                        else:
                            argvols.append(vol)
                    else:
                        argvols.append(vol)
                c.argvols = argvols

    def build(self, name='', opts=''):
        if name:
            self.aliasmap[name].build_image()
            return

        for c in self.containers:
            if getattr(c, 'build', ''):
                c.build_image()

    def pull(self, name='', opts=''):
        if name:
            self.aliasmap[name].pull_image()
            return

        for c in self.containers:
            if getattr(c, 'image', ''):
                c.pull_image()

    def setup(self, name='', opts=''):
        self.pull()
        self.build()
        
    def _status_single(self, container):
        c = container
        ports = c.scan
        if ports:
            addr = client.inspect_container(c.full_name)\
                   ['NetworkSettings']['IPAddress']
            res = True
            for port in ports:
                res = res and scan(addr, port)
                if not res:
                    break
        else:
            res = client.inspect_container(c.full_name)\
                  ["State"]["Running"]
        return res

    def status(self, name='', opts=''):
        output = {True: 'up', False: 'down'}

        for c in self.containers:
            # TODO: return a dictionary that is printed in main
            try:
                res = self._status_single(c)
            except:
                res = False
            print("{}\t\t{}".format(c.name, output[res]))

    def run(self, name='', opts=''):
        if name:
            self.aliasmap[name].run()
            return

        for c in self.containers:
            if not c.standalone:
                c.run()
                time.sleep(0.2)

    def start(self, name='', opts=''):
        if name:
            self.aliasmap[name].start()
            return

        for c in self.containers:
            c.start()

    def stop(self, name='', opts=''):
        if name:
            self.aliasmap[name].stop()
            return

        for c in reversed(self.containers):
            c.stop()

    def restart(self, name='', opts=''):
        # if name:
        #     self.aliasmap[name].restart_container()
        #     return

        # for c in self.containers:
        #     c.restart_container()
        self.stop()
        self.start()

    def pause(self, name='', opts=''):
        if name:
            self.aliasmap[name].pause()
            return

        for c in reversed(self.containers):
            c.pause()

    def unpause(self, name='', opts=''):
        if name:
            self.aliasmap[name].unpause()
            return

        for c in self.containers:
            c.unpause()

    def kill(self, name='', opts=''):
        if name:
            self.aliasmap[name].kill()
            return

        for c in self.containers:
            c.kill()

    def rm(self, name='', opts=''):
        if name:
            self.aliasmap[name].rm()
            return

        for c in self.containers:
            c.rm()

    def rmo(self, name='', opts=''):
        if name:
            self.aliasmap[name].rmo()
            return

        for c in self.containers:
            c.rmo()

    def rmi(self, name='', opts=''):
        if name:
            self.aliasmap[name].rmi()
            return

        for c in self.containers:
            if getattr(c, 'build', ''):
                c.rmi()

    def bash(self, name, opts=''):
        cname = self.aliases[name]
        cmd = 'docker exec -it {} /bin/bash -c "{}"'.format(cname, opts)
        os.system(cmd)

    def shell(self, name, opts=''):
        con = self.aliasmap[name]
        cmd = 'docker exec -it {} {} -c "{}"'.format(con.full_name, con.shell, opts)
        os.system(cmd)


#-------------------------------------------------------------------------------

USAGE = '''docker-master MODE [options] [arguments]
'''

def _main(*args):
    if not args:
        print(USAGE)
        sys.exit(1)

    mode = args[0]
    opts = ' '.join(args[1:])

    config = os.path.join(os.getcwd(), 'master.yml')
    with open(config, 'r') as f:
        app = Application.from_yaml(f)

    if len(args) >= 2:
        name = args[1]
    else:
        name = ''
    opts = ' '.join(args[2:])

    if mode == 'setup':
        app.setup(name, opts)
    elif mode == 'build':
        app.build(name, opts)
    elif mode == 'pull':
        app.pull(name, opts)
    elif mode == 'status':
        app.status(name, opts)
    elif mode == 'start':
        app.start(name, opts)
    elif mode == 'stop':
        app.stop(name, opts)
    elif mode == 'restart':
        app.restart(name, opts)
    elif mode == 'pause':
        app.pause(name, opts)
    elif mode == 'unpause':
        app.unpause(name, opts)
    elif mode == 'run':
        app.run(name, opts)
    elif mode == 'kill':
        app.kill(name, opts)
    elif mode == 'rm':
        app.rm(name, opts)
    elif mode == 'rmo':
        app.rmo(name, opts)
    elif mode == 'rmi':
        app.rmi(name, opts)
    elif mode == 'bash':
        app.bash(name, opts)
    elif mode == 'shell':
        app.shell(name, opts)
    # TODO: make the semantics of these match docker-compose
    elif mode == 'up':
        app.run(name, opts)
    elif mode == 'down':
        app.rm(name, opts)
    elif mode == 'validate':
        print('Validation successful')
    else:
        print(USAGE)
        sys.exit(1)

def main():
    _main(*sys.argv[1:])
