# oauth-stuff

Some utilities to enable oauth login to a Linux machine.

## Requirements

- You need to run the online web connector service somewhere, or you can use https://connector.kxes.net
- You need to run a local server on the PC which caches the protected response from the OAuth endpoint and provides a username/token pair for PAM authentication
- You need to run the PAM module to verify the username/token pair with the local server
- You need to run the NSS module which quieries the local server for passwd information

## Installation

- Copy nw.js distribution to greeter/lightdm-oauth-greeter/nwjs/
- Copy server.py to /usr/sbin/oauth-server.py
- Copy PAM module to /etc/pam.d/oauth_linux.py
- Copy upstart job to /etc/init/oauth-server.conf

## PAM setup

### common-auth

The following line should be placed *below* pam_unix.so (so that pam_unix will handle the token capture first)

`auth sufficient pam_python.so /etc/pam.d/oauth_linux.py`

### common-account

Add the following lines, this time placed *above* pam_unix.so

```
account sufficient pam_python.so /etc/pam.d/oauth_linux.py
```

## The process

Login greeter will redirect a browser to the online web connector service to perform OAuth. The auth token is returned in JSON format and the login greeter should pick this up and pass it to the local OAuth manager server. 

When we made the initial request to the local oauth manager server, it will have performed the protected resource request using the auth token and created a local user account, caching a hash of the auth token in /etc/oauth/users.

It returns a username and password combination that the login greeter should pick up and can automate submission to faciliate PAM authentication.

The PAM module then validates the hash against the local oauth manager server to allow the login to take place unmodified. It does so separately to pam_unix, so you can set a local password for the account that would allow you to log in without an internet connection.