from client_config import ClientConfig
from pyupdater.client import Client
import os, sys
from pyupdater.client.updates import _gen_user_friendly_version as pyu_format_version
from dsdev_utils.helpers import Version as pyu_Version

ROOT_DIR = os.path.dirname(__file__)
if getattr(sys, 'frozen', False):
    ROOT_DIR = sys._MEIPASS

CHANNEL = "alpha"
APP_NAME = 'CL Helper'
with open(os.path.join(ROOT_DIR,'config','version')) as file:
    APP_VERSION = file.readline()

#LIB_NAME = 'Github Repo'
#LIB_VERSION = '0.1.0alpha4'

class Upgrade():

    def __init__(self):
        self.status = ""
        self.totalProgress = 0
        self.client = Client(ClientConfig(), refresh=True)
        self.client.add_progress_hook(self.progress_handler)

    def auto_update(self, channel=CHANNEL):
        app_update = self.check_for_update(channel=channel)
        if app_update:
            self.install(app_update)

    def install(self,update=None, callback=None):
        downloaded = update.download()
        if downloaded:
            if callback is not None:
                callback()
            update.extract_restart()

    def check_for_update(self, channel=CHANNEL, callback=None):
        update = self.client.update_check(APP_NAME,APP_VERSION,channel=channel)
        if callback:
            callback(update)
            return
        return update

    def progress(self):
        return (self.status, self.totalProgress)

    def progress_handler(self, info):
        self.totalProgress = info.get('percent_complete')
        self.status = info.get('status')


    @staticmethod
    def format_version(internal_version):
        return pyu_format_version(str(pyu_Version(internal_version)))

