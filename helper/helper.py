from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import schedule
import time
import requests
import logging.config
import datetime
from dateutil import parser
import dateutil.relativedelta
import json
import os
import sys
from sys import platform
import pytz
from . import google_auth
import base64
from pyquery import PyQuery as pq
from .google_api import Goog
import traceback as tb
import getpass
from appdirs import user_log_dir, user_data_dir

#this is a comment

logDir = user_log_dir('CL Helper','s_murphy') #os.path.join(os.getcwd(),"log")
dataDir = user_data_dir('CL Helper','s_murphy')

ROOT_DIR = os.path.join(os.path.dirname(__file__),"..")
if getattr(sys,'frozen',False):
    ROOT_DIR = sys._MEIPASS
DATA_DIR = dataDir 

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

#if not os.path.exists(logDir):
#    os.makedirs(logDir)
#with open(os.path.join(configDir,'log.json')) as file:
#    logging.config.dictConfig(json.load(file))
log = logging.getLogger("cl_helper")
CHROMEDRIVER_PATH = ""
if platform == 'darwin':
    CHROMEDRIVER_PATH = os.path.join(ROOT_DIR,'drivers','macOS','chromedriver')
elif platform == 'win32':
    CHROMEDRIVER_PATH = os.path.join(ROOT_DIR,'drivers','win','chromedriver.exe')
CL_BASE = "http://accounts.craigslist.org"

class Helper:

    def __init__(self,ui_driver=None,login=None):
        self.status = 'Initialized'
        self.config = json.load(open(os.path.join(os.path.dirname(__file__),'config/cl_config.json')))
        self.ui_driver = ui_driver
        self.credentials = None
        self.data_path = os.path.join(DATA_DIR,"posts.json")
        self.pending_posts = []
        self.last_updated = datetime.datetime.now().timestamp()
        self.google_email = ""
        self.paused = False
        self.started = False

        #try:
        #    with open(self.data_path) as file:
        #        pass
        #except FileNotFoundError:
        #    with open(self.data_path,'w+') as file:
        #        pass

        posts = self.get_posts()
        for post in posts:
            if post['status']=='pending':
                self.pending_posts.append(post)
        #print("Helper __init__ - Login provided: " + str(login))
        if login:
            self.set_login(login)
            if login[0].endswith('@gmail.com'):
                self.google_email = login[0]
            else:
                self.google_email = self.config['google']['email']
        return

    def google_login(self,save_user=True, account=None):
        #print ("Logging in with Google email: %s" % self.google_email)
        if account:
            self.set_google_email(account)
        creds = google_auth.get_stored_credentials(self.google_email)
        if creds:
            self.credentials = creds
            if save_user:
                self.save_current_user()
            return "complete"
        try:
            creds = google_auth.get_credentials('bogus','auth')
        except (google_auth.NoRefreshTokenException, google_auth.CodeExchangeException) as e:
            url = ''
            if hasattr(e,'authorization_url'):
                url = e.authorization_url + '&login_hint=' + self.google_email
            self.open_auth_url(url)
            self.save_user = save_user
            return "pending"
            #driver.find_element_by_id("next").click()
            #driver.find_element_by_id("Passwd").send_keys(self.config['google']['pw'])
            #driver.find_element_by_id("signIn").click()
            #time.sleep(2)
            #driver.find_element_by_id("submit_approve_access").click()
            #access_code = driver.find_element_by_id("code").get_attribute("value")
            #if access_code:
            #    log.debug("access code retrieved: " + access_code)
            #    driver.close()
            #    self.config['google']['access_code'] = access_code #need to write this out at some point
            #    creds = google_auth.get_credentials(access_code,"auth")
            #else:
            #    raise
        #self.credentials = creds
        #return

    def get_current_user(self):
        return self.get_login()[0]

    def set_accounts(self,accounts):
        cl_users = {}
        try:
            with open(os.path.join(DATA_DIR,"cl_users.json")) as file:
                try:
                    cl_users = json.load(file)
                except json.decoder.JSONDecodeError:
                    #don't do anything, it's fine.
                    log.info("First time load of cl_users.json")
        except FileNotFoundError:
            log.info("First time load of cl_users.json")
        users = cl_users.keys()
        self.accounts = []
        for account in accounts:
            if account not in users:
                raise Exception('account %s is not avalable' % account)
            self.accounts.append({account: cl_users[account]})
        return 'complete'

    def open_auth_url(self,url):
        log.debug("openeing new webdriver...")
        try:
            driver = webdriver.Chrome(CHROMEDRIVER_PATH)
        except Exception as e:
            log.debug(tb.format_exc())
            return
        self.auth_driver = driver
        driver.implicitly_wait(2)
        driver.get(url)
        return
    
    def complete_auth(self,access_code):
        if self.auth_driver:
            self.auth_driver.close()
        creds = google_auth.get_credentials(access_code,"auth")
        self.credentials = creds
        user_info = google_auth.get_user_info(creds)
        email_address = user_info.get('email')
        if self.save_user:
            self.save_current_user()
        return email_address

    def set_google_email(self, email):
        #print("Google email set: %s" % email)
        self.google_email = email

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def renew(self):
        if self.paused:
            return
        #print("helper.renew running...")
        driver = webdriver.Chrome(CHROMEDRIVER_PATH)
        if len(self.pending_posts):
            for post in self.pending_posts:
                if post['type']=='email':
                    if self.verify_via_email(driver,post['email_address'],post['last_update']):
                        self.upsert_post(post.update({'status': 'reposted', 'last_update': datetime.datetime.now().timestamp()}))
                    #else just leaving it in pending_posts to be picked up next time
        now = datetime.datetime.now().replace(tzinfo=pytz.utc)
        try:
            done = False
            done_done = False
            if not self.started or (hasattr(self,"next_account") and self.next_account):
                self.started = True
                next_account = self.accounts.pop(0)
                self.accounts.append(next_account)
                user = list(next_account.keys())[0]
                self.set_login((user,next_account[user]['password']))
            driver.get(CL_BASE + "/login/home")
            login = self.get_login()
            driver.find_element_by_id("inputEmailHandle").send_keys(login[0])
            driver.find_element_by_id("inputPassword").send_keys(login[1])
            driver.find_element_by_css_selector("button.accountform-btn").click()
            for d in [2,1,0]:
                dateFilter = now - dateutil.relativedelta.relativedelta(months=d)
                if dateFilter.month == 1:
                    dateFilter = dateFilter.strftime("%Y")
                else:
                    dateFilter = dateFilter.strftime("%Y-%m")
                driver.get(CL_BASE + "/login/home?filter_date=" + dateFilter)
                num_of_pages = len(driver.find_elements_by_css_selector("#paginator legend a")) + 1
                for page in range(num_of_pages):
                    driver.get(CL_BASE + "/login/home?filter_page=" + str(num_of_pages - page) + "&filter_date=" + dateFilter + "&show_tab=postings")
                    posts = driver.find_elements_by_xpath("//table[contains(./@class,'accthp_postings')]/tbody/tr[./td[contains(./@class,'status Z')]]")
                    if len(posts)==0:
                        continue
                    oldest_date = datetime.datetime.now().replace(tzinfo=pytz.utc)
                    newest_date = datetime.datetime.now().replace(tzinfo=pytz.utc)
                    oldest_post = None
                    for row in posts:
                        dates = row.find_elements_by_css_selector("td.posteddate time")
                        newest_date = parser.parse(dates[0].get_attribute("datetime"))
                        if len(dates) > 1:
                            for i in range(len(dates)-1):
                                activity_date = parser.parse(dates[i].get_attribute("datetime"))
                                if activity_date < newest_date:
                                    newest_date = activity_date

                        posted_on = newest_date
                        #posted_on = parser.parse(row.find_element_by_css_selector("td.posteddate > time").get_attribute("datetime"))
                        if posted_on < oldest_date:
                            oldest_date = posted_on
                            # need some more checking on repost vs. renew
                            oldest_post = row #row.find_element_by_css_selector("td.buttons form input[name='go']")
                    if oldest_post:
                        post_title = oldest_post.find_element_by_css_selector("td.title a").text
                        post_href = oldest_post.find_element_by_css_selector("td.title a").get_attribute("href")
                        log.info("Oldest post: " + oldest_post.find_element_by_css_selector("td.title a").text)
                        renew_form = oldest_post.find_elements_by_css_selector("form.renew")
                        if renew_form:
                            # renewing the post
                            log.info("Clicking 'renew'")
                            renew_form[0].find_element_by_css_selector("input[name='go']").click()
                            post_id = driver.current_url.split('?')[0].split('/')[-1]
                            link_p = driver.find_elements_by_xpath("//p[contains(.,'Your posting can be seen at')]/a")
                            if link_p:
                                post_href = link_p[0].get_attribute("href")
                            #else:
                            #    post_href = driver.current_url
                            post_updated = datetime.datetime.now().timestamp()
                            self.upsert_post({
                                'type':'email',
                                'account': self.get_current_user(),
                                'status':'renewed',
                                'id':post_id,
                                'title':post_title,
                                'href':post_href,
                                'last_update':post_updated
                            })
                        else:
                            #deleting and re-posting
                            elapsed_time = datetime.datetime.now().replace(tzinfo=pytz.utc) - newest_date
                            if elapsed_time.days < 7:
                                #done - no more to update since last one is up-to-date
                                done = True
                                done_done = True
                                break
                            log.debug("Clicking 'delete' on posts page")
                            oldest_post.find_element_by_css_selector("form.delete input[name='go']").click()
                            #oldest post deleted
                            post_id = driver.current_url.split('?')[0].split('/')[-1]
                            log.debug("Clicking 'repost' on deleted post page")
                            driver.find_element_by_css_selector("div.managebutton form input[name='go']").click()
                            #opens post details for editing before re-posting
                            #change available on date
                            Select(driver.find_element_by_name("moveinMonth")).select_by_value(str(now.month))
                            driver.find_element_by_name("moveinDay").clear()
                            driver.find_element_by_name("moveinDay").send_keys(str(now.day))
                            driver.find_element_by_name("moveinYear").clear()
                            driver.find_element_by_name("moveinYear").send_keys(str(now.year))
                            continues = driver.find_elements_by_css_selector("button[value='Continue']")
                            if not len(continues):
                                log.debug("No 'Continue' button on post details page.")
                                raise
                                link_ps = driver.find_elements_by_xpath("//p[contains(.,'Your posting can be seen at')]/a")
                                if len(link_ps):
                                    post_href = link_ps[0].get_attribute("href")
                                else:
                                    raise
                                self.upsert_post({
                                    'id': post_id,
                                    'account': self.get_current_user(),
                                    'status': 'reposted',
                                    'title': post_title,
                                    'href': post_href,
                                    'last_update': datetime.datetime.now().timestamp()
                                })
                                done = True
                                break
                            else:
                                log.debug("Clicking 'Continue' button on post details page")
                                #'Continue' button is clicked
                                continues[0].click()
                                log.debug("Clicking 'Publish' button on post confirmation page")
                                driver.find_element_by_css_selector("button[value='Continue']").click()
                                email_auth = driver.find_elements_by_xpath("//b[contains(.,'You should receive an email shortly')]")
                                text_auth = None
                                if email_auth:
                                    #raise
                                    #post_id = '' #driver.current_url 
                                    #post_href = '' #driver.current_url
                                    post_updated = datetime.datetime.now().timestamp()
                                    email_address = driver.find_element_by_xpath("//section[contains(./@class,'body')]/div[contains(.,'Email sent to')]/span[contains(./@class,'e')]").text
                                    if not self.verify_via_email(driver,email_address,post_updated):
                                        self.upsert_post({
                                            'type':'email',
                                            'account': self.get_current_user(),
                                            'status':'pending',
                                            'id':post_id,
                                            'title':post_title,
                                            'href':post_href,
                                            'email_address':email_address,
                                            'last_update':post_updated
                                        })
                                    else:
                                        self.upsert_post({
                                            'id':post_id,
                                            'account': self.get_current_user(),
                                            'status':'reposted',
                                            'title':post_title,
                                            'href':post_href,
                                            'last_update':post_updated
                                        })
                                elif text_auth:
                                    code = self.get_text_auth()
                                else:
                                    link_a = driver.find_elements_by_xpath("//li[contains(.,'View your post at')]/a")
                                    if len(link_a):
                                        post_href = link_a[0].get_attribute("href")
                                    self.upsert_post({
                                        'id': post_id,
                                        'account': self.get_current_user(),
                                        'status': 'reposted',
                                        'title': post_title,
                                        'href': post_href,
                                        'last_update': datetime.datetime.now().timestamp()
                                    })
                        done = True
                        break
                if done:
                    if done_done:
                        self.next_account = True
                    break
        except:
            #driver.close()
            log.error("Error: ", sys.exc_info()[0])
            raise
        #raise #just need to stop driver from closing
        driver.close()

    def get_text_auth(self):
        endpoint = self.config['text_auth']['retrieve']['endpoint']
        data = requests.get(endpoint)
        path = self.config['text_auth']['retrieve']['message_path'].split('.')
        msg = data
        for part in path:
            msg = msg[part]
        msg_re = re.complie(r"secret code for %s is ([0-9]*)\." % self.get_current_user(), re.IGNORECASE)
        res = msg_re.findall(msg)
        return res[0]

    def set_login(self,login):
        self.config.update({
            'craigslist': {
                'credentials': {
                    'user': login[0],
                    'pw': login[1]
                }
            }
        })

    def get_login(self):
        return (self.config['craigslist']['credentials']['user'], self.config['craigslist']['credentials']['pw'])

    def verify_via_email(self,driver,email_address,email_time):
        if self.credentials is None:
            self.google_login()
        self.Goog = api = Goog(self.credentials)
        tries = 0
        maxTries = 12
        while True:
            tries+=1
            q = "from:robot@craigslist.org" + " after:" + str(int(email_time.timestamp()())) #"{:%Y-%m-%d %H:%M:%S}".format(email_time)
            msgs = api.list_messages(self.config['google']['email'],q)
            if not len(msgs):
                time.sleep(5)
                if tries < maxTries:
                    continue
                else:
                    return False
            msg = api.get_message(self.config['google']['email'],msgs[0]['id'])
            msg_body = str(base64.urlsafe_b64decode(msg['raw'].encode("ASCII")))
            html_st = msg_body.find("<html>")
            html_end = msg_body.find("</html>") + len("</html>")
            html = msg_body[html_st:html_end]
            doc = pq(html)
            link = doc("a").attr("href")
            #driver = webdriver.Chrome(CHROMEDRIVER_PATH)
            driver.get(link)
            #potential for text auth

            accept = driver.find_element_by_xpath("//section[contains(./@class,'previewButtons')]/form/button[contains(.,'ACCEPT')]")
            if accept:
                accept.click()
            else:
                #assuming no accept means text auth. Can't get to the screen for a better check.
                number = self.config['text_auth']['number']
                driver.find_element_by_name("n").send_keys(number[0])
                driver.find_element_by_name("n2").send_keys(number[1])
                driver.find_element_by_name("n3").send_keys(number[2])
                driver.find_element_by_css_selector("input[name='callType'][value='sms']").click()
                #this is a guess since I can't find the page
                driver.find_element_by_css_selector("button[type='submit']").click()
                time.sleep(5)
                code = self.get_text_auth()
                #need to put in the code and submit it now, but again, no access to the page, frustratingly
                driver.find_element_by_css_selector("input[name='code']").send_keys(str(code))
                driver.find_element_by_css_selector("button[type='submit']").click()
            driver.close()
            return True
    def get_posts(self,include_time=False):
        data = None
        try:
            with open(self.data_path) as file:
                try:
                    data = json.load(file)
                except json.decoder.JSONDecodeError:
                    data = {}
            if 'posts' not in data:
                data['posts'] = []
            if not include_time:
                return data['posts']
            else:
                data.update({'last_updated':self.last_updated})
                return data
        except FileNotFoundError:
            return []

    @staticmethod
    def get_users():
        user_data = {}
        try:
            with open(os.path.join(DATA_DIR,"cl_users.json"), "r") as file:
                try:
                    user_data = json.load(file)
                except json.decoder.JSONDecodeError:
                    log.info('No loadable data for CL users. Treating as empty.')
            return list(user_data.keys())
        except FileNotFoundError:
            return []

    @staticmethod
    def get_google_users():
        user_data = {}
        try:
            with open(os.path.join(DATA_DIR, "user_data.json")) as file:
                try:
                    user_data = json.load(file)
                except json.decoder.JSONDecodeError:
                    #don't do anything, it's fine.
                    #print("no google users")
                    log.info("First time load of user_data.json")
            return list(user_data.keys())
        except FileNotFoundError:
            return []

    def delete_users(self,users):
        user_data = {}
        try:
            with open(os.path.join(DATA_DIR,"cl_users.json"), "r") as file:
                try:
                    user_data = json.load(file)
                except json.decoder.JSONDecodeError:
                    #don't do anything, it's fine.
                    log.info("First time load of cl_users.json")
        except FileNotFoundError:
            log.info("helper.delete_users - no user file present.")
            return True
        for user in users:
            try:
                del user_data[user]
            except:
                return False
        with open(os.path.join(DATA_DIR,"cl_users.json"), "w+") as file:
            json.dump(user_data,file)
        return True
    
    def save_current_user(self):
        user_data = {}
        try:
            with open(os.path.join(DATA_DIR,"cl_users.json"), "r") as file:
                try:
                    user_data = json.load(file)
                except json.decoder.JSONDecodeError:
                    user_data = {}
        except FileNotFoundError:
            pass
        login = self.get_login()
        user_data[login[0]] = {
            'password': login[1],
            'google_email': self.google_email
        }
        with open(os.path.join(DATA_DIR,"cl_users.json"), "w+") as file:
            user_data = json.dump(user_data,file)
        return

    def add_post(self,post, current_posts=None):
        data = None
        if current_posts == None:
            with open(self.data_path) as data_file:
                try:
                    data = json.load(data_file)
                except json.decoder.JSONDecodeError:
                    data = {}
        else:
            data = {'posts':current_posts}
        data['posts'].insert(0,post)
        if post['status'] == 'pending':
            self.pending_posts.append(post)
        with open(self.data_path,'w+') as file:
            json.dump(data,file)
        self.last_updated = datetime.datetime.now().timestamp()

    def update_post(self,updated_post, current_posts=None):
        #print("updating post: %s" % json.dumps(updated_post))
        posts = current_posts
        if current_posts == None:
            posts = self.get_posts()
        for post in posts:
            if post['id'] == updated_post['id']:
                posts.remove(post)
                break
        posts.insert(0,updated_post)
        data = {'posts': posts}
        with open(self.data_path,'w') as file:
            json.dump(data,file)
        self.last_updated = datetime.datetime.now().timestamp()

    def upsert_post(self,post):
        posts = self.get_posts()
        for ea_post in posts:
            if post['id'] == ea_post['id']:
                self.update_post(post,posts)
                return
        self.add_post(post,posts)

    def submit_logs(self):
        log.info("submitting logs...")
        logTime = datetime.datetime.now()
        if self.credentials is None:
            self.google_login(account='cl.helper01@gmail.com',save_user=False)
        try:
            user = self.get_current_user()
        except KeyError:
            user = "None"
        try:
            osuser = getpass.getuser()
        except Exception:
            osuser = "None"
        msg = {
            'from': self.google_email,
            'to': 'smurphy917@gmail.com',
            'subject': 'CL Helper Logs - %s - %s' % (osuser,logTime.strftime("%Y/%m/%d %H:%M:%S")),
            'body': "LOG FILES ATTACHED FOR USER: %s" % user
        }
        files = [
            os.path.abspath(os.path.join(logDir,'debug.log')),
            os.path.abspath(os.path.join(logDir,'info.log')),
            os.path.abspath(os.path.join(logDir,'errors.log'))
            ]
        print(files)
        api = Goog(self.credentials)
        api.send_message(msg,files=files)

def StartHelper(helper=None,login=None, minutes=6):
    if not helper:
        helper = Helper(login)
    helper.renew()
    schedule.every(minutes).minutes.do(helper.renew)

    while 1:
        schedule.run_pending()
        time.sleep(1)