import sys
import os
import main, init_config, upgrade
from threading import Thread
import logging
import logging.config
import json
import time
import traceback as tb

bundled = False
if getattr(sys, 'frozen', False):
    bundled = True

init_config.init()
#if bundled:
#    upgrade.upgrade()

log = logging.getLogger('main_script')
log.info("main_script Initialized")

def run_main(args=None):
    log.info('Starting main_script...')
    sys.argv = [sys.argv[0] if len(sys.argv) else ''] + ['runserver'] + sys.argv[2:]
    t = Thread(target=main.manager.run)
    t.daemon = True
    log.info('Starting server thread...')
    t.start()
    log.info('Starting client...')
    main.Application.open_page()
    log.info('Closing...')
    try:
        if not main.Application.restarting():
            sys.exit(0)
        else:
            log.debug("starting restart waiting loop...")
            while 1:
                time.sleep(10)
    except SystemExit:
        pass
    except:
        log.debug("Error condition exit.")
        log.error(tb.format_exc())
        raise

run_main()