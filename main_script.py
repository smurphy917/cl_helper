import sys, os, logging
import main, init_config, upgrade
import traceback as tb
import multiprocessing
from multiprocessing import Process, Queue, Pipe, current_process, freeze_support
from multiprocessing.managers import BaseManager, BaseProxy, AutoProxy, listener_client, dispatch, MakeProxyType
from multiprocessing.connection import wait
import psutil
import setproctitle
import time
from helper_ui.app import HelperUI
from helper.helper import Helper
from types import MethodType

init_config.init()

log = logging.getLogger('main_script')
log.info("main_script Initialized")
setproctitle.setproctitle("CLMain")

def RebuildProxyNoReferent(func, token, serializer, kwds):
    #http://stackoverflow.com/questions/29788809/python-how-to-pass-an-autoproxy-object
    '''
    Function used for unpickling proxy objects.

    If possible the shared object is returned, or otherwise a proxy for it.
    '''
    incref = (
        kwds.pop('incref', True) and
        not getattr(multiprocessing.current_process(), '_inheriting', False)
    )
    return func(token, serializer, incref=incref, **kwds)

def AutoCLProxy(token, serializer, manager=None, authkey=None, exposed=None, incref=True):
    proxy = AutoProxy(token, serializer, manager=manager, authkey=authkey, exposed=exposed, incref=incref)
    def reduce_method(self):
        ret = super(type(proxy),self).__reduce__()
        # RebuildProxy is the first item in the ret tuple.
        # So lets replace it, just for our proxy.
        ret = (RebuildProxyNoReferent,) + ret[1:]
        return ret
    proxy.__reduce__ = MethodType(reduce_method,proxy)
    return proxy

class CLManager(BaseManager):
    @classmethod
    def register(cls, *args, **kwargs):
        if 'proxytype' not in kwargs or kwargs['proxytype'] is None:
            kwargs['proxytype'] = AutoCLProxy
        super().register(*args, **kwargs)

class CLRootMain:

    def __init__(self):        
        log.debug("CLRootMain.__init__()")

        CLManager.register('CLServer',main.CLServer)
        CLManager.register('CLClient',main.CLClient)
        CLManager.register('HelperUI',HelperUI)
        CLManager.register('Upgrade',upgrade.Upgrade)
        CLManager.register('Helper', Helper) 

        self.connections = []

        conn, app_conn = Pipe()
        self.connections.append(conn)
        conn, server_conn = Pipe()
        self.connections.append(conn)
        conn, upgrade_conn = Pipe()
        self.connections.append(conn)
        conn, client_conn = Pipe()
        self.connections.append(conn)

        
        self.manager = CLManager()
        self.manager.start()

        self.upgrade = self.manager.Upgrade(connection=server_conn)
        self.helper = self.manager.Helper()
        self.app = self.manager.HelperUI(
            version=upgrade.APP_VERSION,
            helper=self.helper,
            connection=app_conn,
            upgrade = self.upgrade)
        self.server = self.manager.CLServer(
            app=self.app,
            upgrade=self.upgrade,
            connection=server_conn)
        self.client = self.manager.CLClient(connection=client_conn)
        
    def pkill(self,pid=None):
        #recursively kill the whole damn family
        if pid is None:
            pid = current_process().pid
        try:
            p = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return
        for child in p.children():
            self.pkill(child.pid)
        try:
            p.terminate()
        except psutil.NoSuckProcess:
            return
    
    '''
    def start_server(connection=None):
        log.debug(connection)
        server = main.CLServer(version=upgrade.APP_VERSION, connection=connection)
        setproctitle.setproctitle("CLServer")
        #queue.put(server)
        server.run()

    def start_client():
        client = main.CLClient()
        setproctitle.setproctitle("CLClient")
        client.start()

    def monitor():
        count = 0
        while 1:
            time.sleep(1)
    '''

    def close(self):
        #self.manager.shutdown()
        for c in self.connections:
            c.send('KILL')
        self.pkill()

    def run(self):
        log.debug("main_script.CLRootMain.run()")
        #Process(name='CLServer',target=self.server.run).start()
        #Process(name='CLClient',target=self.client.start).start()
        Process(name='CLServer', target=self.server.run).start()
        Process(name='CLClient', target=self.client.start).start()
        
        while self.connections:
            for c in wait(self.connections):
                try:
                    p = c.recv()
                except EOFError:
                    self.connections.remove(c)
                else:
                    log.debug(p)
                    if 'call_method' in p:
                        getattr(self,p['call_method']['method'])(*p['call_method']['args'],**p['call_method']['kwargs'])

            
    
    '''
    def run_main(args=None):
        #init current Process
        #q = Queue()
        multiprocessing.freeze_support()
        connection, child_connection = Pipe()
        #create server
        #log.debug("Create server")
        #server = main.CLServer(version=upgrade.APP_VERSION)
        #create client
        #log.debug("Create client")
        #client = main.CLClient(server=server)
        #start server
        log.debug("Create and start server process")
        p_server = Process(target=start_server, kwargs={'connection': child_connection})
        p_server.name="CL Server"
        p_server.start()
        #start client
        log.debug("Create and start client process")
        p_client = Process(target=start_client)
        p_client.name="CL Client"
        p_client.start()
        #join client
        #log.debug("Join processes")
        #p_client.join()
        log.debug("Monitoring child processes")
        while 1:
            if connection.poll(1):
                p = connection.recv()
                if p['message'] == 'install':
                    p = connection.send({'message': 'install_upgrade'})
                elif p['message'] == 'install_complete':
                    pkill(p_server.pid)
                    pkill(p_client.pid)

        #pkill(p_server.pid)    
    '''

if __name__ == "__main__":
    freeze_support()
    main = CLRootMain()
    main.run()