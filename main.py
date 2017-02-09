from sys import platform
#import helper_ui.app as app
import selenium
from selenium import webdriver
from threading import Thread
import time, os
import flask_script
import logging
import json
import sys
import traceback as tb
from multiprocessing import Process
import upgrade
from helper import helper
import setproctitle

DESIRED_CAPABILITIES = {'chromeOptions': {'args': ['--app=http://127.0.0.1:5000']}}
CHROMEDRIVER_PATH = ""

ROOT_DIR = os.path.dirname(__file__)
if getattr(sys,'frozen',False):
    ROOT_DIR = sys._MEIPASS

if platform == 'darwin':
    CHROMEDRIVER_PATH = os.path.join(ROOT_DIR,'drivers','macOS','chromedriver')
elif platform == 'win32':
    CHROMEDRIVER_PATH = os.path.join(ROOT_DIR,'drivers','win','chromedriver.exe')

log = logging.getLogger("main")

class CLServer:
    def __init__(self,app=None,upgrade=None, connection=None):
        log.debug("Initializing server")
        log.debug(repr(app))
        log.debug(repr(upgrade))
        self.parent_conn = connection
        log.debug("CLServer app: %s" % repr(app))
        self.app = app
        self.upgrade = upgrade
        
    def run(self):
        setproctitle.setproctitle("CLServer")
        log.debug("CLServer run()")
        Process(name="CLHelperUI", target=self.app.run).start()
        update = self.upgrade.check_for_update()
        #self.app.set_update(update)
    @staticmethod
    def connection_monitor(connection, app, upgrade):
        while 1:
            if connection.poll(1):
                p = connection.recv()
                if p['message'] == 'install_upgrade':
                    upgrade.install(app.update)
                    connection.send({'message':'install_complete'})
    #def get_manager(self):
    #    return self.app_proxy.get_manager()
    def restarting(self):
        return self.app.restarting()

class CLClient:
    def __init__(self, connection=None):
        if connection is not None:
            self.conn = connection
    def start(self):
        setproctitle.setproctitle("CLClient")
        self.open_page()
    def open_page(self):
        log.debug("Opening client")
        log.debug("creating driver...")
        try:
            self.driver = webdriver.Chrome(CHROMEDRIVER_PATH, desired_capabilities=DESIRED_CAPABILITIES)#, service_log_path=os.path.join(ROOT_DIR,"log","service_log.log"))
        except Exception as e:
            log.error(tb.format_exc())
            sys.exit(1)
        log.debug("driver created")
        self.main_handle = self.driver.current_window_handle
        self.driver.implicitly_wait(0.1)
        while self.driver_open():
            if self.conn.poll(1):
                p = self.conn.recv()
                if p == 'KILL':
                    self._kill = True
                    break
        log.debug("Client closing")
        self.close()
        return
    def driver_open(self):
        try:
            self.driver.switch_to.window(self.main_handle)
            return True
        except selenium.common.exceptions.NoSuchWindowException:
            self.driver.quit()
            return False
        except Exception as e:
            self.driver.quit()
            return False
    def close(self):
        if not getattr(self,'_kill',False):
            self.conn.send({
                'call_method':{
                    'method': 'close',
                    'args': [],
                    'kwargs': {}
                }
            })
        self.driver.quit()