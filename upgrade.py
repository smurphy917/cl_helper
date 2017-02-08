from client_config import ClientConfig
from pyupdater.client import Client
import os, sys, logging
from pyupdater.client.updates import _gen_user_friendly_version as pyu_format_version
from dsdev_utils.helpers import Version as pyu_Version
from multiprocessing import current_process

ROOT_DIR = os.path.dirname(__file__)
BUNDLED = False
if getattr(sys, 'frozen', False):
    ROOT_DIR = sys._MEIPASS
    BUNDLED = True

CHANNEL = "alpha"
APP_NAME = 'CL Helper'
with open(os.path.join(ROOT_DIR,'config','version')) as file:
    APP_VERSION = file.readline()

log = logging.getLogger()

#LIB_NAME = 'Github Repo'
#LIB_VERSION = '0.1.0alpha4'

class Upgrade():

    def __init__(self, connection=None):
        log.debug("Upgrade initializing")
        self.status = ""
        self.totalProgress = 0
        self.client = Client(ClientConfig())
        self.client.add_progress_hook(self.progress_handler)
        if connection is not None:
            self.conn = connection

    def auto_update(self, channel=CHANNEL):
        app_update = self.check_for_update(channel=channel)
        if app_update:
            self.install(app_update)

    def install(self,update=None, callback=None):
        if not BUNDLED:
            log.debug("Running non-bundled. Not installing updated version.")
            self.status, self.totalProgress = ("Complete", 100)
            if callback is not None:
                callback()
            #JUST TESTING
            log.debug(current_process())
            self.conn.send({
                'call_method':{
                    'method':'close',
                    'args':[],
                    'kwargs':{}
                }
            })
            return
        downloaded = update.download()
        if downloaded:
            if callback is not None:
                callback()
            Process(target=update.extract_restart)
            self.conn.send({
                'call_method':{
                    'method':'close',
                    'args':[],
                    'kwargs':{}
                }
            })

    def check_for_update(self, channel=CHANNEL, callback=None, connection=None):
        self.client.refresh()
        update = self.client.update_check(APP_NAME,APP_VERSION,channel=channel)
        if connection:
            p = {'method':callback,'args':[update]}
            connection.send(p)
            return
        elif callback:
            callback(update)
        return update

    def progress(self):
        return (self.status, self.totalProgress)

    def progress_handler(self, info):
        self.totalProgress = info.get('percent_complete')
        self.status = info.get('status')


    @staticmethod
    def format_version(internal_version):
        return pyu_format_version(str(pyu_Version(internal_version)))

