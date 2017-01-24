import sys
import os
import main, init_config
from threading import Thread
import logging
import logging.config
import json

init_config.init()

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
    sys.exit(0)

run_main()