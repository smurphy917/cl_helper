import logging, os, json
from logging import config
from appdirs import user_data_dir

with open(os.path.join(user_data_dir("CL Helper","s_murphy"),"log.json")) as file:
    config.dictConfig(json.load(file))

from googleapiclient import discovery_cache
c = discovery_cache.autodetect()