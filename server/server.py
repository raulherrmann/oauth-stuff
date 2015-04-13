#!/usr/bin/env python

import os
import json
import time
import hashlib
import requests
import requests.auth
import ConfigParser
import subprocess
from pwd import getpwnam 
from flask import Flask, request, abort, Response

app = Flask(__name__)

USER_CACHE = {}

OAUTH_UID = 10706
OAUTH_GROUP = 3060
OAUTH_STORE_PATH = "/etc/oauth/users"


store = None


class RedisStore:

    def __init__(self):
        raise NotImplementedError


class LocalStore:

    def __init__(self):
        self.configpath = OAUTH_STORE_PATH
        self.config = ConfigParser.SafeConfigParser()
        if not os.path.exists(self.configpath):
            self.sync()
        self.config.read(self.configpath)

    def sync(self):
        f = open(self.configpath,'w')
        self.config.write(f)
        f.close()

    def has_user(self, pw_name):
        return pw_name in self.config.sections()

    def update_user(self, pw_name, uid, service, tokenhash):
        if not pw_name in self.config.sections():
            self.config.add_section(pw_name)
        self.config.set(pw_name, "uid", str(uid))
        self.config.set(pw_name, "service", service)
        self.config.set(pw_name, "tokenhash", tokenhash)
        self.config.set(pw_name, "time", str(time.time()))

    def check(self, pw_name, tokenhash):
        if not pw_name in self.config.sections():
            return False
        if app.debug:
            if self.config.get(pw_name, "tokenhash").startswith(tokenhash):
                return True
            else:
                return False
        else:
            if tokenhash == self.config.get(pw_name, "tokenhash"):
                return True
            else:
                return False

    def getuid(self):
        running = OAUTH_UID
        useruid = 0
        for user in self.config.sections():
            useruid = self.config.getint(user, "uid")
            if useruid >= running:
                running = useruid + 1
        return running


def create_user(pw_name, pw_gecos, oauth_service, oauth_token, tokhash):
    # create a local user account if it doesn't already exist
    if not store.has_user(pw_name):
        uid = store.getuid()
    else:
        uid = store.config.getint(pw_name, "uid")
    # check if unix user exists
    try:
        getpwnam(pw_name)
    except KeyError:
        # user needs creating
        subprocess.Popen("useradd --create-home --no-user-group --uid "+str(uid)+" "+pw_name, shell=True).wait()
    # store the user's oauth service and key hash
    store.update_user(pw_name, uid, oauth_service, tokhash)
    store.sync()
    

def oauth_user_details(service, access_token):
    # send for user info endpoint
    headers = {"User-Agent": "KX Web Connector Local Server"}
    if service == "microsoft":
        response = requests.get("https://apis.live.net/v5.0/me?access_token="+access_token, headers=headers)
    elif service == "google":
        response = requests.get("https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token="+access_token, headers=headers)
    else:
        abort(501)
    me = response.json()
    # check for an error response
    if "error" in me:
        abort(401)
    # extract email to use as username
    if "emails" in me:
        username = me['emails']['preferred'] #.replace("@", ".")
    elif "email" in me:
        username = me['email'] #.replace("@", ".")
    else:
        username = me['id']
    # extract full name to use as gecos
    if "name" in me:
        gecos = me['name']
    else:
        gecos = ""
    # cache user
    tokhash = hashlib.sha1(access_token).hexdigest()
    create_user(username, gecos, service, access_token, tokhash)
    # return the token hash and the username we picked
    return tokhash, username

@app.route('/pre')
def pre():
    oauth_service = request.args.get("service")
    oauth_token = request.args.get("token")
    # send for user details
    tokhash, username = oauth_user_details(oauth_service, oauth_token)
    # return the hash that we made
    return Response(json.dumps({'username': username, 'hash': tokhash}),  mimetype='application/json')

@app.route('/remotepre')
def remotepre():
    oauth_service = request.args.get("service")
    oauth_token = request.args.get("token")
    # send for user details
    tokhash, username = oauth_user_details(oauth_service, oauth_token)
    page = """
        <title>OAUTH %s %s</title>
        """ % (username, tokhash)
    # instead of returning JSON, return some javascript that will pass the values out
    return Response(page,  mimetype='text/html')

@app.route('/check')
def check():
    user = str(request.args.get("user"))
    oauth_tokenhash = str(request.args.get("tokenhash"))
    # the PAM module will make this request
    if store.has_user(user):
        if store.check(user, oauth_tokenhash):
            return Response(json.dumps({'status': 'authorized'}),  mimetype='application/json')
        else:
            abort(403)
    else:
        abort(404)


if __name__ == "__main__":
    store = LocalStore()
    app.debug = True
    app.run(host="localhost", port=9669)