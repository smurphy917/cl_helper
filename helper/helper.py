from selenium import webdriver
from selenium.webdriver.common.keys import Keys
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
import pytz
from . import google_auth
import base64
from pyquery import PyQuery as pq
from .google_api import Goog

CURR_DIR = ""
if hasattr(sys,'frozen'):
    CURR_DIR = sys.prefix
else:
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
logDir = os.path.join(os.getcwd(),"log")
if not os.path.exists(logDir):
    os.makedirs(logDir)
logging.config.dictConfig(json.load(open(os.path.join(CURR_DIR,'config/log.json'))))
log = logging.getLogger("cl_helper")
CHROMEDRIVER_PATH = '/Users/smurphy917/Downloads/chromedriver'
CL_BASE = "http://accounts.craigslist.org"

class Helper:

    def __init__(self,ui_driver=None,login=None):
        self.status = 'Initialized'
        self.config = json.load(open(os.path.join(os.path.dirname(__file__),'config/cl_config.json')))
        self.ui_driver = ui_driver
        self.credentials = None
        self.data_path = os.path.join(CURR_DIR,"data/posts.json")
        self.pending_posts = []
        self.last_updated = datetime.datetime.now().timestamp()
        self.google_email = ""
        self.paused = False
        self.started = False
        posts = self.get_posts()
        for post in posts:
            if post['status']=='pending':
                self.pending_posts.append(post)
        print("Helper __init__ - Login provided: " + str(login))
        if login:
            self.set_login(login)
            if login[0].endswith('@gmail.com'):
                self.google_email = login[0]
            else:
                self.google_email = self.config['google']['email']
        return

    def google_login(self,save_user=True, account=None):
        print ("Logging in with Google email: %s" % self.google_email)
        if account:
            self.set_google_email(account)
        creds = google_auth.get_stored_credentials(self.google_email)
        if creds:
            self.credentials = creds
            if save_user:
                self.save_current_user()
            return "complete"
        try:
            creds = google_auth.get_credentials(self.config['google']['access_code'],'auth')
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
        with open(os.path.join(CURR_DIR,"data/cl_users.json")) as file:
            try:
                cl_users = json.load(file)
            except json.decoder.JSONDecodeError:
                #don't do anything, it's fine.
                log.info("First time load of user_data.json")
        users = cl_users.keys()
        self.accounts = []
        for account in accounts:
            if account not in users:
                raise Exception('account %s is not avalable' % account)
            self.accounts.append({account: cl_users[account]})
        return 'complete'

    def open_auth_url(self,url):
        driver = webdriver.Chrome(CHROMEDRIVER_PATH)
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
        print("Google email set: %s" % email)
        self.google_email = email

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def renew(self):
        if self.paused:
            return
        print("helper.renew running...")
        driver = webdriver.Chrome(CHROMEDRIVER_PATH)
        if len(self.pending_posts):
            for post in self.pending_posts:
                if post['type']=='email':
                    self.verify_via_email(driver,post['email_address'],post['last_update'])
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
                dateFilter = "%i-%i" % (dateFilter.year,dateFilter.month)
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
                            elapsed_time = datetime.datetime.now() - newest_date
                            if elapsed_time.days < 7:
                                #done - no more to update since last one is up-to-date
                                done = True
                                done_done = True
                                break
                            log.info("Clicking 'delete'")
                            oldest_post.find_element_by_css_selector("form.delete input[name='go']").click()
                            #post_href = driver.current_url
                            post_id = driver.current_url.split('?')[0].split('/')[-1]
                            #post_href = "http://dallas.craigslist.org/sdf/apa/%s.html" % post_id
                            print("href: " + post_href + ", id: " + post_id)
                            driver.find_element_by_css_selector("div.managebutton form input[name='go']").click()
                            continues = driver.find_elements_by_css_selector("button[value='Continue']")
                            if not len(continues):
                                link_ps = driver.find_elements_by_xpath("//p[contains(.,'Your posting can be seen at')]/a")
                                if len(link_ps):
                                    post_href = link_ps[0].get_attribute("href")
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
                                continues[0].click()
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
                                    post_href = driver.find_element_by_xpath("//li[contains(.,'View your post at')]/a").get_attribute("href")
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
        twilio_endpoint = self.config['text_auth']['twilio']['endpoint']
        phone_number = self.config['text_auth']['phone_number']
        twilio_auth = (self.config['text_auth']['twilio']['user'],self.config['text_auth']['twilio']['pw'])
        messages = requests.get(twilio_endpoint,params={'DateSent':'{:%y-%m-%d}'.format(datetime.datetime.now()),'to':phone_number},auth=twilio_auth).json
        log.info("auth code message: " + messages[0]['body'])
        code = messages[0]['body'] #will need additional parsing
        raise NotImplementedError
        return code

    def set_login(self,login):
        self.config['craigslist']['credentials']['user'] = login[0]
        self.config['craigslist']['credentials']['pw'] = login[1]

    def get_login(self):
        return (self.config['craigslist']['credentials']['user'], self.config['craigslist']['credentials']['pw'])

    def verify_via_email(self,driver,email_address,email_time):
        if self.credentials is None:
            self.google_login()
        api = Goog(self.credentials)
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
            accept = driver.find_element_by_xpath("//section[contains(./@class,'previewButtons')]/form/button[contains(.,'ACCEPT')]")
            if accept:
                accept.click()
            driver.close()
            return True
    def get_posts(self,include_time=False):
        data = None
        with open(self.data_path) as file:
            try:
                data = json.load(file)
            except json.decoder.JSONDecodeError:
                data = {}
        if not include_time:
            return data['posts']
        else:
            data.update({'last_updated':self.last_updated})
            return data

    @staticmethod
    def get_users():
        user_data = {}
        with open(os.path.join(CURR_DIR,"data/cl_users.json"), "r") as file:
            try:
                user_data = json.load(file)
            except json.decoder.JSONDecodeError:
                log.info('No loadable data for CL users. Treating as empty.')
        return list(user_data.keys())

    @staticmethod
    def get_google_users():
        user_data = {}
        with open(os.path.join(CURR_DIR, "data/user_data.json")) as file:
            try:
                user_data = json.load(file)
            except json.decoder.JSONDecodeError:
                #don't do anything, it's fine.
                print("no google users")
                log.info("First time load of user_data.json")
        return list(user_data.keys())

    def delete_users(self,users):
        user_data = {}
        with open(os.path.join(CURR_DIR,"data/cl_users.json"), "r") as file:
            try:
                user_data = json.load(file)
            except json.decoder.JSONDecodeError:
                #don't do anything, it's fine.
                log.info("First time load of user_data.json")
        for user in users:
            try:
                del user_data[user]
            except:
                return False
        with open(os.path.join(CURR_DIR,"data/cl_users.json"), "w") as file:
            json.dump(user_data,file)
        return True
    
    def save_current_user(self):
        user_data = {}
        with open(os.path.join(CURR_DIR,"data/cl_users.json"), "r") as file:
            try:
                user_data = json.load(file)
            except json.decoder.JSONDecodeError:
                user_data = {}
        login = self.get_login()
        user_data[login[0]] = {
            'password': login[1],
            'google_email': self.google_email
        }
        with open(os.path.join(CURR_DIR,"data/cl_users.json"), "w") as file:
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
        with open(self.data_path,'w') as file:
            json.dump(data,file)
        self.last_updated = datetime.datetime.now().timestamp()

    def update_post(self,updated_post, current_posts=None):
        print("updating post: %s" % json.dumps(updated_post))
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

def StartHelper(helper=None,login=None, minutes=6):
    print("Helper Starting...")
    if not helper:
        print("StartHelper: no helper provided, creating one from login")
        helper = Helper(login)
    print("callable: " + str(hasattr(helper.renew,'__call__')))
    helper.renew()
    schedule.every(minutes).minutes.do(helper.renew)

    while 1:
        schedule.run_pending()
        time.sleep(1)