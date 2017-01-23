from apiclient import errors
from apiclient.discovery import build
import httplib2
import json
import sys
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# ...

class Goog:
    def __init__(self,credentials):
        self.credentials = credentials
        self.http = httplib2.Http()
        self.http = credentials.authorize(self.http)
        self.service = build('gmail', 'v1', http=self.http)

    def list_messages(self, user, query=''):
        """Gets a list of messages.

        Args:
            service: Authorized Gmail API service instance.
            user: The email address of the account.
            query: String used to filter messages returned.
                Eg.- 'label:UNREAD' for unread Messages only.

        Returns:
            List of messages that match the criteria of the query. Note that the
            returned list contains Message IDs, you must use get with the
            appropriate id to get the details of a Message.
        """
        try:
            response = self.service.users().messages().list(userId=user, q=query).execute()
            messages = []
            if 'messages' in response:
                messages = response['messages']

            while 'nextPageToken' in response:
                page_token = response['nextPageToken']
                response = self.service.users().messages().list(userId=user, q=query,
                                                pageToken=page_token).execute()
                messages.extend(response['messages'])

            return messages
        except (errors.HttpError) as error:
            print ('An error occurred: %s' % error)
            if error.resp.status == 401:
                # Credentials have been revoked.
                # TODO: Redirect the user to the authorization URL.
                raise NotImplementedError()

    def get_message(self,user,message_id,format='raw'):
        message = self.service.users().messages().get(userId=user,id=message_id,format=format).execute()
        return message

    def send_message(self,user,msg,files=None):
        if not len(files):
            msg_obj = MIMEText(msg['body'])
        else:
            msg_obj = MIMEMultipart()
            msg_body = MIMEText(msg['body'])
            msg_obj.attach(msg_body)
            for file in files:
                msg_obj.attach(file)
        msg_obj['to'] = msg['to']
        msg_obj['from'] = msg['from']
        msg_obj['subject'] = msg['subject']
        if len(files):
            for file in files:
                msg_obj.attach(file)
        msg_final = {
            'raw': base64.urlsafe_b64encode(str.encode(msg_obj.as_string())).decode("utf-8")
        }
        #print(json.dumps(msg_final, indent=2))
        res = self.service.users().messages().send(
            userId='me',
            body=msg_final,
        ).execute()
        print(res)