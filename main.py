#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# __author__ = 'Liantian'
# __email__ = "liantian.me+code@gmail.com"
#
# Copyright 2015-2016 liantian
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org>


import os
import json
import random
import string
import base64
from datetime import datetime
from io import BytesIO, StringIO

from google.appengine.ext import ndb
from google.appengine.api import app_identity
from google.appengine.api import mail

from flask import Flask
from flask import request, render_template
from flask_wtf.csrf import CSRFProtect

import qrcode

from models import ShadowsocksServer, ActivationCode
from forms import CodeForm

app = Flask(__name__)
if 'SERVER_SOFTWARE' in os.environ and os.environ['SERVER_SOFTWARE'].startswith('Dev'):
    app.config['DEBUG'] = True

app.secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(32))
app.config['SESSION_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(32))
app.config['WTF_CSRF_SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(32))
app.config['SITE_URL'] = 'https://static.liantian.me'

csrf = CSRFProtect()
csrf.init_app(app)


@app.errorhandler(404)
def page_not_found(e):
    return "Error : 404 - Page Not Found", 404


@app.route('/', methods=('GET', 'POST'))
def index():
    form = CodeForm()
    if form.validate_on_submit():
        # 处理激活码
        act_code = ActivationCode.query(ActivationCode.code == form.code.data.upper(),
                                        ActivationCode.enable == True).get()
        act_code.enable = False
        act_code.user = form.email.data
        act_code.used = datetime.now()

        # 读取服务器
        ss_server = ShadowsocksServer.query(ShadowsocksServer.user == None).get()
        ss_server.user = form.email.data

        # 生成页面
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=4, border=1)
        uri = "{0}:{1}@{2}:{3}".format(ss_server.method, ss_server.password, ss_server.server, ss_server.server_port)
        data = "ss://{0}#{1}".format(base64.b64encode(uri).replace('\n', '').replace('=', ''), ss_server.remarks.replace('#', '%23'))
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image()
        f = BytesIO()
        img.save(f, format='PNG')
        f.seek(0)
        img_byte = f.read()
        img_string = base64.b64encode(img_byte)
        # 存储
        ndb.put_multi([act_code, ss_server])

        # 发送邮件
        try:
            message = mail.EmailMessage()
            message.sender = 'noreply@{0}.appspotmail.com'.format(app_identity.get_application_id())
            message.subject = "{0} info".format(ss_server.remarks)
            message.to = form.email.data
            message.attachments = [("qr.png", img_byte)]
            message.body = """
server:{0}
server_port:{1}
method:{2}
password:{3}
the qrcode as attachments
                """.format(ss_server.server, ss_server.server_port, ss_server.method, ss_server.password)
            message.html = """
<html><head></head><body>
    <h1>{0}</h1>
    <p>Server:<span>{1}</span></p>
    <p>Port:<span>{2}</span></p>
    <p>method:<span>{3}</span></p>
    <p>password:<span>{4}</span></p>
    <p>QRCode:</p>
    <p>
    <img src="data:image/png;base64,{5}" />
    </p>
    <p>the qrcode also as attachments</p>
</body></html>
            """.format(ss_server.remarks,
                       ss_server.server,
                       ss_server.server_port,
                       ss_server.method,
                       ss_server.password,
                       img_string)
            message.send()
        except:
            pass

        return render_template("show.html", ss_server=ss_server, img_string=img_string), 200
    return render_template("index.html", form=form)


@app.route('/admin/')
def admin():
    all_server = ShadowsocksServer.query().fetch()
    all_act_code = ActivationCode.query().fetch()
    return render_template("admin.html", all_server=all_server, all_act_code=all_act_code)


@app.route('/admin/add_code', methods=['POST'])
def add_code():
    try:
        num = int(request.values.get('num'))
        if num < 1 or num > 10:
            num = 1
        i = 0
        code_list = []
        while i < num:
            code = ''.join(random.choice('2346789BCDFGHJKMPQRTVWXY') for i in range(12))
            act_code = ActivationCode()
            act_code.code = code
            code_list.append(act_code)
            i += 1
        ndb.put_multi(code_list)
        return render_template("info.html", msg="OK! add multi "), 200
    except:
        return render_template("info.html", msg="not int"), 555


@app.route('/admin/add_server', methods=['POST'])
def add_server():
    if 'file' not in request.files:
        return render_template("info.html", msg="No file part"), 555
    file = request.files['file']
    stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
    servers = json.load(stream)
    if isinstance(servers, dict):
        try:
            s = ShadowsocksServer()
            s.server = servers["server"]
            s.server_port = servers["server_port"]
            s.method = servers["method"]
            s.password = servers["password"]
            s.remarks = servers["remarks"]
            s.put()
            return render_template("info.html", msg="OK! add one "), 200
        except:
            return render_template("info.html", msg="ERROR! "), 555
    elif isinstance(servers, list):
        try:
            server_list = []
            for server in servers:
                s = ShadowsocksServer()
                s.server = server["server"]
                s.server_port = server["server_port"]
                s.method = server["method"]
                s.password = server["password"]
                s.remarks = server["remarks"]
                server_list.append(s)
            ndb.put_multi(server_list)
            return render_template("info.html", msg="OK! add multi "), 200
        except:
            return render_template("info.html", msg="ERROR! "), 555
    else:
        return render_template("info.html", msg="ERROR! No Json file "), 555

