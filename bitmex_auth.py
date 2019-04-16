    
import time
from requests.auth import AuthBase
import hashlib
import hmac
from urllib.parse import urlparse


class AccessTokenAuth(AuthBase):

    """Attaches Access Token Authentication to the given Request object."""

    def __init__(self, accessToken):
        """Init with Token."""
        self.token = accessToken

    def __call__(self, r):
        """Called when forming a request - generates access token header."""
        if (self.token):
            r.headers['access-token'] = self.token
        return r

class APIKeyAuthWithExpires(AuthBase):

    """Attaches API Key Authentication to the given Request object. This implementation uses `expires`."""

    def __init__(self, apiKey, apiSecret):
        """Init with Key & Secret."""
        self.apiKey = apiKey
        self.apiSecret = apiSecret

    def __call__(self, r):
        """
        Called when forming a request - generates api key headers. This call uses `expires` instead of nonce.
        This way it will not collide with other processes using the same API Key if requests arrive out of order.
        For more details, see https://www.bitmex.com/app/apiKeys
        """
        # modify and return the request
        expires = int(round(time.time()) + 5)  # 5s grace period in case of clock skew
        r.headers['api-expires'] = str(expires)
        r.headers['api-key'] = self.apiKey
        r.headers['api-signature'] = generate_signature(self.apiSecret, r.method, r.url, expires, r.body or '')

        return r

class APIKeyAuth(AuthBase):

    """Attaches API Key Authentication to the given Request object."""

    def __init__(self, apiKey, apiSecret):
        """Init with Key & Secret."""
        self.apiKey = apiKey
        self.apiSecret = apiSecret

    def __call__(self, r):
        """Called when forming a request - generates api key headers."""
        # modify and return the request
        nonce = generate_nonce()
        r.headers['api-expires'] = str(nonce)
        r.headers['api-key'] = self.apiKey
        r.headers['api-signature'] = generate_signature(self.apiSecret, r.method, r.url, nonce, r.body or '')

        return r


def generate_nonce():
    return int(round(time.time() + 3600))


# Generates an API signature.
# A signature is HMAC_SHA256(secret, verb + path + nonce + data), hex encoded.
# Verb must be uppercased, url is relative, nonce must be an increasing 64-bit integer
# and the data, if present, must be JSON without whitespace between keys.
#
# For example, in psuedocode (and in real code below):
#
# verb=POST
# url=/api/v1/order
# nonce=1416993995705
# data={"symbol":"XBTZ14","quantity":1,"price":395.01}
# signature = HEX(HMAC_SHA256(secret, 'POST/api/v1/order1416993995705{"symbol":"XBTZ14","quantity":1,"price":395.01}'))
def generate_signature(secret, verb, url, nonce, data):
    """Generate a request signature compatible with BitMEX."""
    # Parse the url so we can remove the base and extract just the path.
    parsedURL = urlparse(url)
    path = parsedURL.path
    if parsedURL.query:
        path = path + '?' + parsedURL.query

    if isinstance(data, (bytes, bytearray)):
        data = data.decode('utf8')

    # print "Computing HMAC: %s" % verb + path + str(nonce) + data
    message = verb + path + str(nonce) + data

    signature = hmac.new(bytes(secret, 'utf8'), bytes(message, 'utf8'), digestmod=hashlib.sha256).hexdigest()
    return signature
