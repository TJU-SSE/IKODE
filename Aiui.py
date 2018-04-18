# -*- coding: utf-8 -*-
"""
    jQuery Example
    ~~~~~~~~~~~~~~

    A simple application that shows how Flask and jQuery get along.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
# from flask import Flask, jsonify, render_template, request
# import urllib2
# import time
# import urllib
# import json
# import hashlib
# import base64
#
# from VP import VP
#
#
#
# app = Flask(__name__)
#
#
# @app.route('/_add_numbers')
# def add_numbers():
#     """Add two numbers server side, ridiculous but well..."""
#     a = request.args.get('a', 0, type=int)
#     b = request.args.get('b', 0, type=int)
#
#     f = open("/Users/likun/PycharmProjects/aiui/test.wav", 'rb')
#     file_content = f.read()
#     base64_audio = base64.b64encode(file_content)
#     body = urllib.urlencode({'audio': base64_audio})
#
#     url = 'http://api.xfyun.cn/v1/service/v1/iat'
#     api_key = '33d9e16b6ce345e4caa7e9523030851d'
#     param = {"engine_type": "sms16k", "aue": "raw"}
#
#     x_appid = '5ad58881'
#     x_param = base64.b64encode(json.dumps(param).replace(' ', ''))
#     x_time = int(int(round(time.time() * 1000)) / 1000)
#     x_checksum = hashlib.md5(api_key + str(x_time) + x_param).hexdigest()
#     x_header = {'X-Appid': x_appid,
#                 'X-CurTime': x_time,
#                 'X-Param': x_param,
#                 'X-CheckSum': x_checksum}
#     req = urllib2.Request(url, body, x_header)
#     result2 = urllib2.urlopen(req)
#     result2 = result2.read()
#     print result2
#
#     return jsonify(result=a + b, result2 = result2)
#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
# if __name__ == '__main__':
#     app.run()


# -*- coding:utf-8 -*-
from flask import Flask, jsonify, render_template, request
import base64
import sys
import time
import json
import hashlib

from VP import VP
from IP import IP

img_count = 0

app = Flask(__name__, static_url_path='')



@app.route('/_store_img', methods=['POST'])
def store_img():
    pass
    a = {}
    a['result'] = "ok",
    a['file'] = "name.png"


    i = IP()


    a['img_result'] = i.get_imgs()

    return json.dumps(i.get_imgs())

@app.route('/_add_numbers')
def add_numbers():
    """Add two numbers server side, ridiculous but well..."""
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)

    v = VP()
    r = v.webiat()
    print(json.loads(r)['data'])

    return jsonify(result = r)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
