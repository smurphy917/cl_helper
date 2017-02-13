from googleapiclient import errors
from googleapiclient.discovery import build
import httplib2
import json
import sys
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
import mimetypes
import os
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

    def send_message(self,msg,files=None):
        if not len(files):
            msg_obj = MIMEText(msg['body'])
        else:
            msg_obj = MIMEMultipart()
            msg_body = MIMEText(msg['body'])
            msg_obj.attach(msg_body)
            for f in files:
                content_type, encoding = mimetypes.guess_type(f)
                if content_type is None or encoding is not None:
                    content_type = 'application/octet-stream'
                main_type, sub_type = content_type.split('/', 1)
                if main_type == 'text':
                    with open(f, 'r') as fp:
                        attachment = MIMEText(fp.read(), _subtype=sub_type)
                elif main_type == 'image':
                    with open(f, 'r') as fp:
                        attachment = MIMEImage(fp.read(), _subtype=sub_type)
                elif main_type == 'audio':
                    with open(f, 'r') as fp:
                        attachment = MIMEAudio(fp.read(), _subtype=sub_type)
                else:
                    attachment = MIMEBase(main_type, sub_type)
                    with open(f, 'r') as fp:
                        attachment.set_payload(fp.read())
                filename = os.path.basename(f)
                if filename.endswith('.log'):
                    filename+= '.txt'
                attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                msg_obj.attach(attachment)
        msg_obj['to'] = msg['to']
        msg_obj['from'] = msg['from']
        msg_obj['subject'] = msg['subject']
        msg_final = {
            'raw': base64.urlsafe_b64encode(str.encode(msg_obj.as_string())).decode("utf-8")
        }
        res = self.service.users().messages().send(
            userId='me',
            body=msg_final,
        ).execute()