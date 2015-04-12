#
# PAM module for KX Web Auth Connector
#

import requests

def pam_sm_authenticate(pamh, flags, argv):
    try:
        user = pamh.get_user(None)
        token = pamh.authtok
    except pamh.exception, e:
        return e.pam_result
    response = requests.get("http://127.0.0.1:9669/check?tokenhash="+pamh.authtok);
    if response.status_code == 200:
        return pamh.PAM_SUCCESS
    return pamh.PAM_AUTH_ERR

def pam_sm_setcred(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_acct_mgmt(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_open_session(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_close_session(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_chauthtok(pamh, flags, argv):
    return pamh.PAM_SUCCESS
