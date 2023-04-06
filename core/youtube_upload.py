import http.client
import httplib2
import os
import random
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
                        http.client.IncompleteRead, http.client.ImproperConnectionState,
                        http.client.CannotSendRequest, http.client.CannotSendHeader,
                        http.client.ResponseNotReady, http.client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google Developers Console at
# https://console.developers.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "credential/client_secret.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_DELETE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE).replace('\\', '/'))

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


def get_authenticated_service(args):
    #
    # flow = OAuth2WebServerFlow(client_id='1027445482699-1ujfqumakstu1hsd315baq61nms3u6jo.apps.googleusercontent.com',
    #                        client_secret='LzY4nyyLE2J2OyKWKcHcHmt7',
    #                        scope=YOUTUBE_UPLOAD_SCOPE,
    #                        redirect_uri='http://skigit.com/')
    # auth_uri = flow.step1_get_authorize_url()
    flow = flow_from_clientsecrets(os.path.join(
        os.path.dirname(__file__), CLIENT_SECRETS_FILE).replace('\\', '/'),
                                   scope=YOUTUBE_UPLOAD_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)
    # flow.params['access_type'] = 'offline'
    # import argparse
    # from oauth2client import tools
    #
    # parser = argparse.ArgumentParser(parents=[tools.argparser])
    # flags = parser.parse_args()
    # print '*'*60
    # print flags

    storage = Storage(os.path.join(
        os.path.dirname(__file__), 'skigit_project/youtube-oauth2.json').replace('\\', '/'))
#    credentials = storage.get()
    credentials  = client.Credentials.new_from_json('{"_module": "oauth2client.client", "scopes": ["https://www.googleapis.com/auth/youtube.upload"], "token_expiry": "2017-01-28T18:30:19Z", "id_token": null, "access_token": "ya29.GlzhAzRl94J846U49a31NGnNpCEtjn3kUhX0Pe7aCVSupTvEqNawNW-3Qi4ermSHPHMZxMuGiGmUyRlPvKrceZRzzR6R0QagnUDob16U_zVyJexXOTd-V1uNiBDmMA", "token_uri": "https://accounts.google.com/o/oauth2/token", "invalid": false, "token_response": {"access_token": "ya29.GlzhAzRl94J846U49a31NGnNpCEtjn3kUhX0Pe7aCVSupTvEqNawNW-3Qi4ermSHPHMZxMuGiGmUyRlPvKrceZRzzR6R0QagnUDob16U_zVyJexXOTd-V1uNiBDmMA", "token_type": "Bearer", "expires_in": 3600}, "client_id": "1027445482699-dhl7q18cmj6j0hjl5gespsna15psot57.apps.googleusercontent.com", "token_info_uri": "https://www.googleapis.com/oauth2/v3/tokeninfo", "client_secret": "s2C_kpMINYzrVYWFxm7rudZM", "revoke_uri": "https://accounts.google.com/o/oauth2/revoke", "_class": "OAuth2Credentials", "refresh_token": "1/t-U8ON5oDp7y_MMWoPOG2xFC1GqB5nSdyVGNoazfvGA", "user_agent": null}')

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)
        # credentials.revoke(httplib2.Http())
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    response['message'] = "<span style='font-size:20px;'><i class='glyphicon glyphicon-ok-circle' style='top: 5px !important;' /></span> Your video '%s' was successfully uploaded. You will be notified when posted." % response['id']
                    response['status'] = True
                    return response
                else:
                    response['status'] = False
                    response['message'] = "The upload failed with an unexpected response: %s" % response
                    return response
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
                response['status'] = False
                response['message'] = 'HttpError'
                response['error'] = error
                return response
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e
            response['status'] = False
            response['message'] = 'RETRIABLE_EXCEPTIONS'
            response['error'] = error
            return response
        if error is not None:
            response['status'] = False
            response['error'] = error
            retry += 1
            if retry > MAX_RETRIES:
                response['message'] = 'No longer attempting to retry.'
                return response
            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            response['message'] = "Sleeping %f seconds and then retrying..." % sleep_seconds
            time.sleep(sleep_seconds)
            return response


def initialize_upload(youtube, options):
    tags = None
    if options.keywords:
        tags = options.keywords.split(",")

    body = dict(
        snippet=dict(
            title=options.title,
            description=options.description,
            tags=tags,
            categoryId=options.category
        ),
        status=dict(
            privacyStatus=options.privacyStatus
        )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )
    video_entry = resumable_upload(insert_request)
    return video_entry

    # This method implements an exponential backoff strategy to resume a
    # failed upload.


def delete_video(video_id):
    #flow = flow_from_clientsecrets('client_secret.json',
    #                               scope=['https://www.googleapis.com/auth/youtube'],
    #                               message=MISSING_CLIENT_SECRETS_MESSAGE)

    #storage = Storage(os.path.join(
    #    os.path.dirname(__file__), 'cridential/youtube-oauth2.json').replace('\\', '/'))
    # credentials = storage.get()
    #credentials = client.Credentials.new_from_json(
    #    '{"_module": "oauth2client.client", "scopes": ["https://www.googleapis.com/auth/youtube"],"token_expiry": "2017-01-30T13:07:58Z", "id_token": null, "access_token": "ya29.GlvjA1rUWshG05-j4XdG7mcT8-oZgjexOn2Oo9s25ARGr5XVppKFNj9TUd-8jQ_iMFEkK6OhbRt3eS6UpzqjzWof02Uv0qqY6zyvGjOjYDS8xf5FI6OEMteRPBnV", "token_uri": "https://accounts.google.com/o/oauth2/token", "invalid": false, "token_response": {"access_token": "ya29.GlvjA1rUWshG05-j4XdG7mcT8-oZgjexOn2Oo9s25ARGr5XVppKFNj9TUd-8jQ_iMFEkK6OhbRt3eS6UpzqjzWof02Uv0qqY6zyvGjOjYDS8xf5FI6OEMteRPBnV", "token_type": "Bearer", "expires_in": 3600, "refresh_token": "1/LdTD6dfl-nHyZXXaado30whmvvVOnhrTtGUgGcvMbcQ"}, "client_id": "1027445482699-dhl7q18cmj6j0hjl5gespsna15psot57.apps.googleusercontent.com", "token_info_uri": "https://www.googleapis.com/oauth2/v3/tokeninfo", "client_secret": "s2C_kpMINYzrVYWFxm7rudZM", "revoke_uri": "https://accounts.google.com/o/oauth2/revoke", "_class":"OAuth2Credentials", "refresh_token": "1/LdTD6dfl-nHyZXXaado30whmvvVOnhrTtGUgGcvMbcQ", "user_agent": null}')

    #if credentials is None or credentials.invalid:
    #    credentials = run_flow(flow, storage)
        # credentials.revoke(httplib2.Http())
    #youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    #                http=credentials.authorize(httplib2.Http()))

    b2 = B2Storage()
    try:
        delete_request = b2.delete(file_id=video_id, name=name)
    except:
        # don't have permission to delete the video
        pass


def upload_direct(file, title, description, privacyStatus=VALID_PRIVACY_STATUSES[2]):

    import argparse
    parser = argparse.ArgumentParser(parents=[argparser])
    parser.add_argument("--file", help="Video file to upload")
    parser.add_argument("--title",  help="Video title", default='Skigit Video')
    parser.add_argument("--description", help="Video description", default='Skigit Description')
    parser.parse_args(["--description", description])
    parser.add_argument("--category", default="22", help="Numeric video category. " +
                                                         "See https://developers.google.com/youtube/v3/docs/videoCategories/list")
    parser.add_argument("--keywords",  help="Video keywords, comma separated", default="")
    parser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES, default=VALID_PRIVACY_STATUSES[2], help="Video privacy status.")
    args = parser.parse_args(["--file", file, "--title", title, "--description", description,
                              "--privacyStatus", privacyStatus])

    if not os.path.exists(args.file):
        responce = {}
        responce['message'] = "Please specify a valid file"
        responce['error'] = "%s is not valid file. Check your file extantion or type" % args.file
        responce['status'] = False
        return responce

    youtube = get_authenticated_service(args)
    try:
        video_entry = initialize_upload(youtube, args)
        return video_entry
    except HttpError as e:
        responce = {}
        responce['message'] = 'In Direct Upload (upload_direct) an HTTP error occurred'
        responce['error'] = "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
        responce['status'] = False
        return responce
