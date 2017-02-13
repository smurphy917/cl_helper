import logging
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import Credentials
from googleapiclient.discovery import build
import httplib2
import sys, os
import json
from appdirs import user_data_dir
# ...


# Path to client_secrets.json which should contain a JSON document such as:
#   {
#     "web": {
#       "client_id": "[[YOUR_CLIENT_ID]]",
#       "client_secret": "[[YOUR_CLIENT_SECRET]]",
#       "redirect_uris": [],
#       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#       "token_uri": "https://accounts.google.com/o/oauth2/token"
#     }
#   }
ROOT_DIR = os.path.join(os.path.dirname(__file__),'..')
if getattr(sys,"frozen",False):
  ROOT_DIR = sys._MEIPASS

DATA_DIR = user_data_dir('CL Helper','s_murphy')

CLIENTSECRETS_LOCATION = os.path.join(ROOT_DIR,'helper','config','client_id.google.json')
REDIRECT_URI = "http://localhost:5000/complete_auth" #"urn:ietf:wg:oauth:2.0:oob"
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    # Add other requested scopes.
]

log = logging.getLogger("cl_helper")

class GetCredentialsException(Exception):
  """Error raised when an error occurred while retrieving credentials.

  Attributes:
    authorization_url: Authorization URL to redirect the user to in order to
                       request offline access.
  """

  def __init__(self, authorization_url):
    """Construct a GetCredentialsException."""
    self.authorization_url = authorization_url


class CodeExchangeException(GetCredentialsException):
  """Error raised when a code exchange has failed."""


class NoRefreshTokenException(GetCredentialsException):
  """Error raised when no refresh token has been found."""


class NoUserIdException(Exception):
  """Error raised when no user ID could be retrieved."""


def get_stored_credentials(user_id):
  """Retrieved stored credentials for the provided user ID.

  Args:
    user_id: User's ID.
  Returns:
    Stored oauth2client.client.OAuth2Credentials if found, None otherwise.
  Raises:
    NotImplemented: This function has not been implemented.
  """
  log.debug("retrieving user credentials for: " + user_id)
  try:
    with open(os.path.join(DATA_DIR, 'user_data.json'), 'r') as file:
        user_data = json.load(file)
        if user_id in user_data:
          return Credentials.new_from_json(json.dumps(user_data[user_id]['stored_credentials']))
        else:
          return None
  except (FileNotFoundError, json.decoder.JSONDecodeError):
    return None
  # TODO: Implement this function to work with your database.
  #       To instantiate an OAuth2Credentials instance from a Json
  #       representation, use the oauth2client.client.Credentials.new_from_json
  #       class method.
  raise NotImplementedError()


def store_credentials(user_id, credentials):
  """Store OAuth 2.0 credentials in the application's database.

  This function stores the provided OAuth 2.0 credentials using the user ID as
  key.

  Args:
    user_id: User's ID.
    credentials: OAuth 2.0 credentials to store.
  Raises:
    NotImplemented: This function has not been implemented.
  """
  user_email = credentials.id_token['email']
  log.debug("storing user credentials for: " + user_email)
  user_data = {}
  try:
    with open(os.path.join(DATA_DIR,'user_data.json'),'r') as file:
        user_data = json.load(file)
  except (FileNotFoundError, json.decoder.JSONDecodeError):
    pass
  if user_id not in user_data:
    user_data[user_id] = {'stored_credentials': {}}
  user_data[user_id]['stored_credentials'] = json.loads(credentials.to_json())
  with open(os.path.join(DATA_DIR,'user_data.json'),'w+') as file:
    json.dump(user_data,file)
  '''
  # TODO: Implement this function to work with your database.
  #       To retrieve a Json representation of the credentials instance, call the
  #       credentials.to_json() method.
  raise NotImplementedError()
  '''

def exchange_code(authorization_code):
  """Exchange an authorization code for OAuth 2.0 credentials.

  Args:
    authorization_code: Authorization code to exchange for OAuth 2.0
                        credentials.
  Returns:
    oauth2client.client.OAuth2Credentials instance.
  Raises:
    CodeExchangeException: an error occurred.
  """
  flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, ' '.join(SCOPES))
  flow.redirect_uri = REDIRECT_URI
  try:
    credentials = flow.step2_exchange(authorization_code)
    return credentials
  except FlowExchangeError as error:
    log.error('An error occurred: %s', error)
    raise CodeExchangeException(None)


def get_user_info(credentials):
  """Send a request to the UserInfo API to retrieve the user's information.

  Args:
    credentials: oauth2client.client.OAuth2Credentials instance to authorize the
                 request.
  Returns:
    User information as a dict.
  """
  log.debug("creating http...")
  http = credentials.authorize(httplib2.Http())
  log.debug("building user info service...")
  user_info_service = build(
      serviceName='oauth2', version='v2',
      http=http)
  user_info = None
  log.debug("getting user info from service...")
  try:
    user_info = user_info_service.userinfo().get().execute()
  except errors.HttpError as e:
    log.error('An error occurred: %s', e)
  if user_info and user_info.get('id'):
    return user_info
  else:
    raise NoUserIdException()


def get_authorization_url(email_address, state):
  """Retrieve the authorization URL.

  Args:
    email_address: User's e-mail address.
    state: State for the authorization URL.
  Returns:
    Authorization URL to redirect the user to.
  """
  flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, ' '.join(SCOPES))
  flow.params['access_type'] = 'offline'
  flow.params['approval_prompt'] = 'force'
  flow.params['user_id'] = email_address
  flow.params['state'] = state
  flow.redirect_uri = REDIRECT_URI
  return flow.step1_get_authorize_url()


def get_credentials(authorization_code, state):
  """Retrieve credentials using the provided authorization code.

  This function exchanges the authorization code for an access token and queries
  the UserInfo API to retrieve the user's e-mail address.
  If a refresh token has been retrieved along with an access token, it is stored
  in the application database using the user's e-mail address as key.
  If no refresh token has been retrieved, the function checks in the application
  database for one and returns it if found or raises a NoRefreshTokenException
  with the authorization URL to redirect the user to.

  Args:
    authorization_code: Authorization code to use to retrieve an access token.
    state: State to set to the authorization URL in case of error.
  Returns:
    oauth2client.client.OAuth2Credentials instance containing an access and
    refresh token.
  Raises:
    CodeExchangeError: Could not exchange the authorization code.
    NoRefreshTokenException: No refresh token could be retrieved from the
                             available sources.
  """
  email_address = ''
  try:
    credentials = exchange_code(authorization_code)
    log.debug("credentials retrieved")
    log.debug("getting user info...")
    user_info = get_user_info(credentials)
    email_address = user_info.get('email')
    user_id = user_info.get('id')
    if credentials.refresh_token is not None:
      store_credentials(email_address, credentials)
      return credentials
    else:
      credentials = get_stored_credentials(email_address)
      if credentials and credentials.refresh_token is not None:
        return credentials
  except CodeExchangeException as error:
    log.error('An error occurred during code exchange.')
    # Drive apps should try to retrieve the user and credentials for the current
    # session.
    # If none is available, redirect the user to the authorization URL.
    error.authorization_url = get_authorization_url(email_address, state)
    raise error
  except NoUserIdException:
    log.error('No user ID could be retrieved.')
  # No refresh token has been retrieved.
  authorization_url = get_authorization_url(email_address, state)
  raise NoRefreshTokenException(authorization_url)