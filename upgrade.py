from client_config import ClientConfig
from pyupdater.client import Client
import os, sys, logging
from pyupdater.client.updates import _gen_user_friendly_version as pyu_format_version
from dsdev_utils.helpers import Version as pyu_Version
from multiprocessing import current_process, Process
from subprocess import Popen

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

class NoAvailableUpdate(Exception):
    pass

def test_restart():
    log.debug("test_restart sys.argv: %s" % sys.argv)
    Popen('python %s' % '-'.join(sys.argv))

class Upgrade():

    def __init__(self, connection=None):
        log.debug("Upgrade initializing")
        self.status = ""
        self.totalProgress = 0
        self._client = Client(ClientConfig())
        self._client.add_progress_hook(self.progress_handler)
        self._update = None
        if connection is not None:
            self.conn = connection

    def auto_update(self, channel=CHANNEL):
        app_update = self.check_for_update(channel=channel)
        if app_update:
            self.install()

    def install(self):
        log.debug('Upgrade.install')
        if self._update is None:
            self.check_for_update()
            if self._update is None:
                raise NoAvailableUpdate("No update is available.")
        log.debug("Upgrade downloading...")
        downloaded = self._update.download()
        log.debug("Upgrade download complete.")
        if downloaded:
            self.status, self.totalProgress = ('Complete',100)
            if BUNDLED:
                p = Process(target=self._update.extract_restart, name='CLInstall')
            else:
                log.debug("Running non-bundled. Update will not be installed.")
                p = Process(target=test_restart, name='CLInstall')
            p.start()
            log.debug("install process started: %s" % p.pid)
            self.conn.send({
                'call_method':{
                    'method':'close',
                    'args':[],
                    'kwargs':{'excl':[p.pid]}
                }
            })

    def check_for_update(self, channel=CHANNEL):
        self._client.refresh()
        self._update = self._client.update_check(APP_NAME,APP_VERSION,channel=channel)
        return self._update

    def get_update(self):
        return self._update

    def progress(self):
        return (self.status, self.totalProgress)

    def progress_handler(self, info):
        self.totalProgress = info.get('percent_complete')
        self.status = info.get('status')


    @staticmethod
    def format_version(internal_version):
        return pyu_format_version(str(pyu_Version(internal_version)))

