"""
Script to upload files into API
Author: Iurii Garmash
"""


import httplib
import urllib
import os
import sys
import re


HOST = "192.168.1.105:8000"
USERNAME = 'admin'
PASSWORD = 'admin'

ERRORS = {
    'no_resp_login': 'Server returned wrong response (Not 200) on login'
}


url = "(?P<url>https?://[^\s]+)"
API_PATH = "/api/file/"
SCRIPT_PATH = os.path.abspath(os.path.split(__file__)[0])

filename = 'ADL-0001.pdf'

def login(connection):
    """
    Logs in client
    """
    CSRF_NAME = "csrfmiddlewaretoken"
    CSRF_REGEXP = """name=['"]""" + CSRF_NAME + """['"]\s+value=['"](?P<data>[^'"]+)"""
    LOGIN_URL = '/accounts/login/'
    # Getting login page
    connection.request("GET", LOGIN_URL)
    response = connection.getresponse()
    if response.status != 200:
        sys.stdout.write(ERRORS['no_resp_login'])
        raise Exception(ERRORS['no_resp_login'])
    # Localising CSRF token
    login_page = response.read()
    csrftoken = re.search(CSRF_REGEXP, str(login_page)).group("data")
    params = urllib.urlencode({
        "username" : USERNAME,
        "password" : PASSWORD,
        CSRF_NAME: csrftoken,})
    print params
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}
    connection.request("POST", LOGIN_URL, params, headers)
    response = connection.getresponse()
    connect_page = response.read()
    print connect_page
    return connection


def post_file():



    params = urllib.urlencode({"username" : USERNAME, "password" : PASSWORD,})

    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}


    conn.request("POST", '/accounts/login/')
    response = conn.getresponse()

    print response.status, response.reason

    data = response.read()
    conn.close()

if __name__ == "__main__":
    c = httplib.HTTPConnection(HOST)
    print 'connected'
    connection = login(c)
    connection.close()
    #post_file()