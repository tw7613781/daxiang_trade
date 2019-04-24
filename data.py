'''
it communicates with Bitmex exchange API, fetch all necessary origin info. 
It also becomes the base class for all classes 
'''

import bitmex
import settings as s
class Data:
    posotion = None
    margin = None

    def __init__(self):
        self.client = bitmex.bitmex(test=s.TEST, api_key=s.API_KEY, api_secret=s.API_SECRET)


