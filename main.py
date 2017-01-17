from sys import platform
from helper_ui.app import HelperUI
import selenium
from selenium import webdriver
import threading
from threading import Thread
import time, os
from flask_script import Server

CHROMEDRIVER_PATH = ""
if platform == 'darwin':
    CHROMEDRIVER_PATH = os.path.join(os.getcwd(),'drivers','macOS','chromedriver')
elif platform == 'win32':
    CHROMEDRIVER_PATH = os.path.join(os.getcwd(),'drivers','win','chromedriver.exe')
DESIRED_CAPABILITIES = {'chromeOptions': {'args': ['--app=http://localhost:5000']}}

class Main(Server):
    def __init__(self):
        self.helperui = HelperUI()
    def __call__(self,app,*args,**kwargs):
        self.helperui.run()
        self.open_page()
        return Server.__call__(self,app,*args,**kwargs)
    def get_manager(self):
        return self.helperui.get_manager()
    def open_page(self):
        time.sleep(3)
        self.driver = webdriver.Chrome(CHROMEDRIVER_PATH, desired_capabilities=DESIRED_CAPABILITIES, service_log_path='/dev/null')
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

class CustomServer(Server):
    def __call__(self,app,*args,**kwargs):
        #Thread(target=main.open_page).start()
        return Server.__call__(self,app,*args,**kwargs)

manager.add_command('runserver',CustomServer)

print("main name: " + __name__)
if __name__ == "__main__":
    manager.run()