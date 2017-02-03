import sys, os, logging
import main, init_config, upgrade
import traceback as tb
import multiprocessing
from multiprocessing import Process, Queue
import psutil
import setproctitle

init_config.init()

log = logging.getLogger('main_script')
log.info("main_script Initialized")
setproctitle.setproctitle("CLMain")

def pkill(pid):
    #recursively kill the whole damn family
    p = psutil.Process(pid)
    for child in p.children():
        pkill(child.pid)
    p.terminate()

def start_server():
    server = main.CLServer(version=upgrade.APP_VERSION)
    setproctitle.setproctitle("CLServer")
    #queue.put(server)
    server.run()

def start_client():
    client = main.CLClient()
    setproctitle.setproctitle("CLClient")
    client.start()

def run_main(args=None):
    #init current Process
    #q = Queue()
    multiprocessing.freeze_support()
    #create server
    #log.debug("Create server")
    #server = main.CLServer(version=upgrade.APP_VERSION)
    #create client
    #log.debug("Create client")
    #client = main.CLClient(server=server)
    #start server
    log.debug("Create and start server process")
    p_server = Process(target=start_server)
    p_server.name="CL Server"
    p_server.start()
    #start client
    log.debug("Create and start client process")
    p_client = Process(target=start_client)
    p_client.name="CL Client"
    p_client.start()
    #join client
    log.debug("Join processes")
    p_client.join()
    pkill(p_server.pid)    

if __name__ == "__main__":
    run_main()