from client_config import ClientConfig
from pyupdater.client import Client

APP_NAME = 'CL Helper'
APP_VERSION = '0.1.0alpha8'

#LIB_NAME = 'Github Repo'
#LIB_VERSION = '0.1.0alpha4'

def upgrade():

    client = Client(ClientConfig(), refresh=True)

    app_update = client.update_check(APP_NAME,APP_VERSION, channel='alpha')
    #lib_update = client.update_check(LIB_NAME, LIB_VERSION)

    if app_update:
        downloaded = app_update.download()
        if downloaded:
            app_update.extract_restart()

