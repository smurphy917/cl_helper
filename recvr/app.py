from flask import Flask, request, make_response
import os
import datetime
import json
import logging.config

app = Flask(__name__)
logging.config.dictConfig(json.load(open(os.path.join(os.path.dirname(__file__),"config/log.json"))))
log = logging.getLogger("recvr")

repoFilePath = "repository.json"

@app.route("/sms",methods=['GET','POST'])
def receive():
    log.info("received JSON: " + str(request.get_json()))
    #log.info("received data: " + str(request.data))
    #log.info("received value: " + json.dumps(request.values))
    newMessage = {'time':'{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()),'data':request.get_json()}
    repository = {}
    with open(repoFilePath,"r+") as repoFile:
        repository = json.load(repoFile)
    if 'incoming' not in repository:
        repository['incoming'] = []
    repository['incoming'].append(newMessage)
    with open(repoFilePath,"w") as repoFile:
        json.dump(repository,repoFile)
    return make_response("",200)

@app.route("/get_last",methods=['GET'])
def retrieve():
    log.info("requested: " + str(request))
    last = {}
    with open(repoFilePath,"r+") as repoFile:
        repository = json.load(repoFile)
        last = repository['incoming'][-1]
    return json.dumps(last)
