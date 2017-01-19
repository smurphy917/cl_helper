from sys import platform
from helper_ui.app import HelperUI
import selenium
from selenium import webdriver
from threading import Thread
import time, os
import flask_script
import logging

DESIRED_CAPABILITIES = {'chromeOptions': {'args': ['--app=http://127.0.0.1:5000']}}
CHROMEDRIVER_PATH = ""
#TEMP
if platform == 'darwin':
    CHROMEDRIVER_PATH = os.path.join(os.getcwd(),'drivers','macOS','chromedriver')
elif platform == 'win32':
    CHROMEDRIVER_PATH = os.path.join(os.getcwd(),'drivers','win','chromedriver.exe')

logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.INFO)

class Main(flask_script.Server):
    def __init__(self):
        self.helperui = HelperUI()
    def __call__(self,app,*args,**kwargs):
        self.helperui.run()
        self.open_page()
        return flask_script.Server.__call__(self,app,*args,**kwargs)
    def get_manager(self):
        return self.helperui.get_manager()
    def open_page(self):
        time.sleep(3)
        self.driver = webdriver.Chrome(CHROMEDRIVER_PATH, desired_capabilities=DESIRED_CAPABILITIES)
        self.main_handle = self.driver.current_window_handle
        self.driver.implicitly_wait(0.1)
        self.helperui.set_driver(self.driver)
        while self.driver_open():
            time.sleep(1)
        print ("done")
    def driver_open(self):
        try:
            self.driver.switch_to.window(self.main_handle)
            return True
        except selenium.common.exceptions.NoSuchWindowException:
            self.driver.quit()
            return False

main = Main()
manager = main.get_manager()

class CustomServer(flask_script.Server):
    def __call__(self,app,*args,**kwargs):
        #Thread(target=main.open_page).start()
        return flask_script.Server.__call__(self,app,*args,**kwargs)

manager.add_command('runserver',CustomServer)

print("main name: " + __name__)
if __name__ == "__main__":
    manager.run()