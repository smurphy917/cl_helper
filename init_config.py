from appdirs import user_log_dir, user_config_dir
import os, json, logging, re

log_dir = user_log_dir('CL Helper','s_murphy')
config_dir = user_config_dir('CL Helper','s_murphy')

class LogFilter(logging.Filter):

    def __init__(self):
        self.requestFiltered = False

    def filter(self,record):
        exp1 = re.compile(r'POST\s*http:\/\/(?:[0-9]*\.){3}[0-9]:[0-9]*\/session\/[a-zA-Z0-9]*\/window')
        exp2 = re.compile(r'Finished Request')
        if exp1.match(record.getMessage()):
            self.requestFiltered = True
            return False
        elif exp2.match(record.getMessage()) and self.requestFiltered:
            return False
        return True

def create_log_config():
    with open(os.path.join('config','log.json')) as file:
        log_config = json.load(file)
    for key, handler in log_config['handlers'].items():
        if 'filename' in handler:
            log_config['handlers'][key]['filename'] = os.path.join(log_dir,handler['filename'].split('/')[-1])
    with open(os.path.join(config_dir,'log.json'), 'w+') as file:
        json.dump(log_config,file)

def config_logging():
    with open(os.path.join(config_dir,'log.json')) as file:
        logging.config.dictConfig(json.load(file))
    logging.getLogger("selenium.webdriver.remote.remote_connection").addFilter(LogFilter())

def init():
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    if not os.path.exists(os.path.join(config_dir,'log.json')):
        create_log_config()

    config_logging()
    
