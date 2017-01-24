import sys
from sys import platform
from flask import Flask, request, make_response, render_template, jsonify
from flask_script import Manager, Command
import os
import datetime
import json
import logging.config
import time
from selenium import webdriver
from helper import helper
from threading import Thread

ROOT_DIR = os.path.join(os.path.dirname(__file__),"..")
if getattr(sys,'frozen',False):
    ROOT_DIR = sys.prefix
#overriding for testing
#ROOT_DIR = os.path.dirname(__file__)
logDir = os.path.join(os.getcwd(),"log")
if not os.path.exists(logDir):
    os.makedirs(logDir)
logging.config.dictConfig(json.load(open(os.path.join(ROOT_DIR,'config','log.json'))))
log = logging.getLogger("helper_ui")

class HelperUI:

    def __init__(self,driver=None, version=None):
        self.driver = driver
        self.status = "Not Started"
        self.version = version
        self.app = Flask(__name__)
        self.app.add_url_rule("/",view_func=self.home,methods=['GET'])
        self.app.add_url_rule("/start",view_func=self.start,methods=['POST'])
        self.app.add_url_rule("/users",view_func=self.get_users,methods=['GET'])
        self.app.add_url_rule("/poll",view_func=self.poll,methods=['GET'])
        self.app.add_url_rule("/complete_auth",view_func=self.complete_auth,methods=['GET','POST'])
        self.app.add_url_rule("/pause",view_func=self.pause,methods=['GET'])
        self.app.add_url_rule("/resume",view_func=self.resume,methods=['GET'])
        self.app.add_url_rule("/add_account",view_func=self.add_account,methods=['POST'])
        self.app.add_url_rule("/add_google_account", view_func=self.add_google_account, methods=['GET'])
        self.app.add_url_rule("/delete_accounts", view_func=self.delete_accounts, methods=['POST'])
        self.app.add_url_rule("/submit_logs", view_func=self.submit_logs, methods=['GET'])
        self.app.add_url_rule("/meta",view_func=self.meta, methods=['GET'])
        self.last_updated = datetime.datetime.now().timestamp()
        self.helper = helper.Helper()

    def set_driver(self,driver):
        self.driver = driver

    def home(self):
        data = {
            'status':{
                'text':'Not started',
                'class': 'not-started'
            },
            'available_users':[
                'Lori.murphy46@yahoo.com'
            ],
            'posts':[
                {
                    'datetime':'12/14/2016 4:32pm',
                    'title': 'Fancy Apartment!!! LOTS of Ameneties !!! YAY!!!',
                    'href': 'https://google.com',
                    'expires': '02/14/2017 4:31pm'
                }
            ]
        }
        return render_template('home.html',data=data)

    def add_account(self):
        reqData = request.get_json()
        user = reqData['user']
        pw = reqData['pw']
        google_account = reqData['google_account']
        if not hasattr(self,'helper'):
            self.helper = helper.Helper(self.driver,login=(user,pw))
        else:
            self.helper.set_login((user,pw))
        status = self.helper.google_login(account=google_account)
        if status=='complete':
            #Thread(target=helper.StartHelper, args=(self.helper,None,period)).start()
            self.status = "User Added Successfully"
            return jsonify({
                'status':'success',
                'account':{
                    'user':user
                }
            })
        else:
            self.status = "Pending Google Authorization"
            self.internal_status = "NEW_CL_ACCOUNT"
            return jsonify({'status': 'Pending Google Authorization'})

    def delete_accounts(self):
        reqData = request.get_json()
        accounts = reqData['accounts']
        success = self.helper.delete_users(accounts)
        if success:
            return jsonify({
                'status': 'success',
                'available_accounts': self.helper.get_users()
                })
        else:
            return jsonify({'status': 'error'})

    def add_google_account(self):
        #print("Adding Google account...")
        reqData = request.get_json()
        email = ""
        if reqData is not None and 'google_account' in reqData:
            email = reqData['google_account']
        #print("Setting google email: %s" % email)
        self.helper.set_google_email(email)
        #print("Loggin in google")
        self.helper.google_login(save_user=False)
        self.internal_status = "NEW_GOOGLE_ACCOUNT"
        return jsonify({'status': 'Pending Google Authorization'})

    def start_new(self):
        reqData = request.get_json()
        period = reqData['period']
        accounts = reqData['accounts']
        self.helper.set_accounts(accounts)
        Thread(target=helper.StartHelper, args=(self.helper,None,period)).start()
        return jsonify({'status':'Running'})

    def start(self):
        log.info("requested: " + str(request))
        reqData = request.get_json()
        if not hasattr(self,'helper'):
            self.helper = helper.Helper(self.driver)
        status = self.helper.set_accounts(reqData['accounts'])
        #status = self.helper.google_login()
        if status=='complete':
            Thread(target=helper.StartHelper, args=(self.helper,None,reqData['period'])).start()
            self.status = "Running"
            return jsonify({'status':'Running'})
        else:
            self.status = "Pending Google Authorization"
            return jsonify({'status': 'Pending Google Authorization'})

    def poll(self):
        data = {}
        posts = []
        last_updated = datetime.datetime.now().timestamp()
        if self.last_updated:
            last_updated = self.last_updated
        if hasattr(self,'helper'):
            if self.helper.status == 'Complete':
                self.status = 'Complete'
            data = self.helper.get_posts(include_time=True)
        else:
            return jsonify({
                'status': 'Stopped'
            })
        if data and 'last_updated' in data.keys():
            last_updated = data['last_updated']
        if data and 'posts' in data.keys():
            posts = data['posts']
        resp = {
            'last_updated': last_updated,
            'posts': posts,
            'status': self.status if self.status else "Running"
        }
        if hasattr(self,'new_google_account'):
            resp['added_google_accounts'] = [self.new_google_account]
            del self.new_google_account
        if hasattr(self,'new_account'):
            resp['added_accounts'] = ['self.new_account']
        return jsonify(resp)

    def complete_auth(self):
        access_code = request.args['code']
        new_google_account = self.helper.complete_auth(access_code)
        self.status = "Google Account Added Successfully"
        #self.status = "Running"
        #Thread(target=helper.StartHelper, args=(self.helper,)).start()
        if self.internal_status == "NEW_CL_ACCOUNT":
            self.new_account = new_google_account
        elif self.internal_status == "NEW_GOOGLE_ACCOUNT":
            self.new_google_account = new_google_account
        self.internal_status = ""
        return make_response(("complete",200,{}))

    def get_users(self):
        resp = helper.Helper.get_users()
        resp_g = helper.Helper.get_google_users()
        res = {'available_users':resp, 'available_google_users': resp_g}
        #print(json.dumps(res))
        return jsonify(res)

    def pause(self):
        self.helper.pause()
        self.status = "Paused"
        resp = {
            'status': 'Paused'
        }
        return jsonify(resp)

    def resume(self):
        self.helper.resume()
        self.status = "Running"
        resp = {
            'status': 'Running'
        }
        return jsonify(resp)

    def run(self):
        self.app.run(debug=True)

    def get_manager(self):
        return Manager(self.app)
    
    def submit_logs(self):
        self.helper.submit_logs()
        return jsonify({'status': 'Logs Submitted'})

    def meta(self):
        return jsonify({
            'version': self.version if self.version else '-'
        })
        

    
