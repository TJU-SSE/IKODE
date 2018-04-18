# -*- coding:utf-8 -*-
from productai import Client
import json
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_STATIC_PATH = os.path.join(APP_ROOT, 'static/')

class IP(object):
    def __init__(self):
        pass

    def get_imgs(self):
        ACCESS_KEY_ID = 'ba80ba232e415f1e7cf163492dcd4f79'
        SECRET_KEY = '0347d65e7bb1c6c42b989ad6703c4690'
        SERVICE_ID = 'f3yhvxqf'

        cli = Client(ACCESS_KEY_ID, SECRET_KEY)
        # Get service API context
        api = cli.get_image_search_api(SERVICE_ID)

        # change service endpoint to HK:
        # cli.url_root = 'https://api-ap-southeast-1.productai.com'

        # call by url
        # resp = api.query(image='http://img.mp.itc.cn/upload/20161225/61163ecbcc7545b6b2ecddccc29f827f_th.jpg')
        # print(resp.content)

        # Call api with local file as input parameter
        with open(os.path.join(APP_STATIC_PATH, 'img/1.jpeg'), mode='rb') as search:
            resp = api.query(search)
        print(resp.content)
        return bytes.decode(resp.content)
