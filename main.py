from sys import platform
from helper_ui.app import HelperUI
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
import upgrade

DESIRED_CAPABILITIES = {'chromeOptions': {'args': ['--app=http://127.0.0.1:5000']}}
CHROMEDRIVER_PATH = ""

ROOT_DIR = os.path.dirname(__file__)
bundled = False
if getattr(sys,'frozen',False):
    ROOT_DIR = sys._MEIPASS
    bundled = True

if platform == 'darwin':
    CHROMEDRIVER_PATH = os.path.join(ROOT_DIR,'drivers','macOS','chromedriver')
elif platform == 'win32':
    CHROMEDRIVER_PATH = os.path.join(ROOT_DIR,'drivers','win','chromedriver.exe')

# setLevel(logging.INFO)
#with open(os.path.join(ROOT_DIR,'config','log.json')) as file:
#    logging.config.dictConfig(json.load(file))
log = logging.getLogger("main")

log.debug("main imported...")

class Main(flask_script.Server):
    def __init__(self,version=None):
        log.debug("main init...")
        self.helperui = HelperUI(version=version)
        log.debug("...done")
    def __call__(self,app,*args,**kwargs):
        self.helperui.run()
        self.open_page()
        return flask_script.Server.__call__(self,app,*args,**kwargs)
    def get_manager(self):
        return self.helperui.get_manager()
    def open_page(self):
        log.debug("main.open_page()...")
        time.sleep(1)
        log.debug("chromedriver path: %s" % CHROMEDRIVER_PATH)
        log.debug("chromedriver exists: %s" % str(os.path.exists(CHROMEDRIVER_PATH)))
        log.debug("creating driver...")
        try:
            self.driver = webdriver.Chrome(CHROMEDRIVER_PATH, desired_capabilities=DESIRED_CAPABILITIES)#, service_log_path=os.path.join(ROOT_DIR,"log","service_log.log"))
        except Exception as e:
            log.error(tb.format_exc())
            sys.exit(1)
        log.debug("driver created")
        self.main_handle = self.driver.current_window_handle
        self.driver.implicitly_wait(0.1)
        self.helperui.set_driver(self.driver)
        while self.driver_open():
            time.sleep(1)
        return
        #print ("done")
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

    def restarting(self):
        return self.helperui.restarting()

Application = Main(version=upgrade.APP_VERSION)
manager = Application.get_manager()

class CustomServer(flask_script.Server):
    def __call__(self,app,*args,**kwargs):
        #Thread(target=main.open_page).start()
        return flask_script.Server.__call__(self,app,*args,**kwargs)

manager.add_command('runserver',CustomServer)

#print("main name: " + __name__)
if __name__ == "__main__":
    manager.run()