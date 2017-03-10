from helper.helper import Helper
from appdirs import user_data_dir
import logging
import logging.config
import os, json

with open(os.path.join(user_data_dir('CL Helper','s_murphy'),'log.json')) as file:
    logging.config.dictConfig(json.load(file))

h = Helper()
h.set_login(('noelle0229@gmail.com','ic2ghc88'))
h.google_login('noelle0229@gmail.com')