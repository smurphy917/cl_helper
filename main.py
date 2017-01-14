from helper_ui.app import HelperUI
from selenium import webdriver
import threading
from threading import Thread
import time, os
from flask_script import Server
CHROMEDRIVER_PATH = '/Users/smurphy917/Downloads/chromedriver'
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
        self.driver = webdriver.Chrome(CHROMEDRIVER_PATH, desired_capabilities=DESIRED_CAPABILITIES)
        self.helperui.set_driver(self.driver)
        #self.driver.get("http://localhost:5000")

main = Main()
manager = main.get_manager()

class CustomServer(Server):
    def __call__(self,app,*args,**kwargs):
        Thread(target=main.open_page).start()
        return Server.__call__(self,app,*args,**kwargs)

manager.add_command('runserver',CustomServer)

print("main name: " + __name__)
if __name__ == "__main__":
    manager.run()

