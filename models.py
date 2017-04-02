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

from google.appengine.ext import ndb

encrypt_method = (
    "aes-128-gcm", "aes-192-gcm", "aes-256-gcm", "rc4-md5", "aes-128-cfb", "aes-192-cfb", "aes-256-cfb", "aes-128-ctr",
    "aes-192-ctr", "aes-256-ctr", "bf-cfb", "camellia-128-cfb", "camellia-192-cfb", "camellia-256-cfb",
    "chacha20-ietf-poly1305", "salsa20", "chacha20", "chacha20-ietf")


class ShadowsocksServer(ndb.Model):
    server = ndb.StringProperty()
    server_port = ndb.IntegerProperty()
    method = ndb.StringProperty(choices=encrypt_method)
    password = ndb.StringProperty(indexed=False)
    remarks = ndb.StringProperty()
    local_port = 1080
    fast_open = True
    timeout = 4
    mode = "tcp_and_udp"
    user = ndb.StringProperty()


class ActivationCode(ndb.Model):
    used = ndb.DateTimeProperty()
    enable = ndb.BooleanProperty(default=True)
    code = ndb.StringProperty()
    user = ndb.StringProperty()
