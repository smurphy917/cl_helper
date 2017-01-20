import sys
import os
import main
from threading import Thread
import logging
import logging.config
import json

logDir = os.path.join(os.getcwd(),"log")
if not os.path.exists(logDir):
    os.makedirs(logDir)

CURR_DIR = os.path.dirname(__file__)
if getattr(sys,'frozen',False):
    CURR_DIR = sys._MEIPASS
with open(os.path.join(CURR_DIR,'config','log.json')) as file:
    logging.config.dictConfig(json.load(file))
log = logging.getLogger('main_script')
log.info("main_script Initialized")

def run_main(args=None):
    log.info('Starting main_script...')
    sys.argv = [sys.argv[0] if len(sys.argv) else ''] + ['runserver'] + sys.argv[2:]
    t = Thread(target=main.manager.run)
    t.daemon = True
    log.info('Starting server thread...')
    t.start()
    log.info('Initializing main...')
    m = main.Main()
    log.info('Starting client...')
    m.open_page()
    log.info('Closing...')

#if __name__ == '__main__':
#    run_main()

run_main()