import json
import ssl
import time
import urllib.request

import Crypto.PublicKey.RSA
import python_jwt as jwt

_accepted_sign_algs = ["PS512"]
_pubkey_cache_living_time = 60*10  # 10min
_pubkey_cache_exp_time = 0
_pubkey_cache = ""


def get_public_key(reauth_url, verify=True):
    """
    Get ReAuth server public key from server.
    It's recommended in production setup to store public key locally for example in configuration.
    :param reauth_url: ReAuth server base url. E.g. https://reauth.example.com
    :param verify: Verify TLS, default value is True
    :return: Public key in text format
    """
    global _pubkey_cache_exp_time, _pubkey_cache, _pubkey_cache_living_time

    if time.time() < _pubkey_cache_exp_time:
        public_key = _pubkey_cache
    else:
        ctx = ssl.create_default_context()
        ctx.check_hostname = verify

        with urllib.request.urlopen(reauth_url + "/key.pub", context=ctx) as f:
            public_key = f.read()
            _pubkey_cache = public_key
            _pubkey_cache_exp_time = time.time() + _pubkey_cache_living_time
    return public_key


def fetch_reauth_token(code, reauth_url, verify=True):
    """
    Fetch ReAuth token from ReAuth server using code passed in redirect.
    :param code: Code
    :param reauth_url: ReAuth server base url. E.g. https://reauth.example.com
    :param verify: Verify TLS, default value is True
    :return: Token in text format
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = verify
    with urllib.request.urlopen(reauth_url.rstrip("/") + "/api/v1/token/" + code + "/", context=ctx) as f:
        data = json.loads(f.read().decode("utf-8"))
        if 'jwtToken' in data:
            return data['jwtToken']
    return None


def decode_reauth_token(token, public_key):
    """
    Decode and verify ReAuth token
    :param token: Token in text format
    :param public_key: Server public key.
    :return: Dictionary containing Claims from token
    """
    public_key = Crypto.PublicKey.RSA.importKey(public_key)
    header, claims = jwt.verify_jwt(token, public_key, _accepted_sign_algs)

    return claims

