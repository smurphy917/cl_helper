from sys import platform
import helper_ui.app as app
import selenium
from selenium import webdriver
from threading import Thread
import time, os
import flask_script
import logging
import json
import sys
import traceback as tb
import subprocess
from multiprocessing.managers import BaseManager
import upgrade
from helper import helper

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

class CLManager(BaseManager):
    pass

class CLServer:
    def __init__(self,version=None):
        log.debug("Initializing server")
        CLManager.register('HelperUI',app.HelperUI)
        CLManager.register('Upgrade',upgrade.Upgrade)
        CLManager.register('Helper',helper.Helper)
        manager = CLManager()
        manager.start()
        self.upgrade = manager.Upgrade()
        self.helper = manager.Helper()
        #Flask app
        self.app = manager.HelperUI(version=version, upgrade=self.upgrade, helper=self.helper)
        #self.app_proxy.set_proxy(self.app_proxy)
        self.app.check_update(proxy=self.app)
    def run(self):
        self.app.run()
    #def get_manager(self):
    #    return self.app_proxy.get_manager()
    def restarting(self):
        return self.app.restarting()

class CLClient:
    def __init__(self):
        pass
    def start(self):
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
            time.sleep(1)
        log.debug("Client closed")
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