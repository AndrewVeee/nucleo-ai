from flask import Flask, request, Response
import importlib
from types import ModuleType
import json
from multiprocessing import Process
import re
import traceback

from api import api

class EndpointAction:
  def __init__(self, app, url, action, kwargs):
    self.url = url
    self.app = app
    self.action = action
    self.opts = kwargs
    self.auth = kwargs['auth'] if 'auth' in kwargs else True

  def update_action(self, action):
    self.app.debug(f"Updating action: {self.url} {action}")
    self.action = action

  def check_auth(self):
    if self.app.server.auth_key is None or self.app.server.auth_key == '':
      return True

    try:
      if 'Authorization' in request.headers:
        result = request.headers['Authorization'].split(' ', 1)
        if result[0].lower() == 'bearer':
          if result[1] == self.app.server.auth_key:
            return True
    except BaseException as e:
      self.app.log("Auth error:", str(e))
      return False

    return False

  def __call__(self, *args):
    self.response = Response(status=200, headers={'Content-Type': 'application/json'})
    if self.auth and not self.check_auth():
      self.response.status = 403
      self.response.response = json.dumps({'error': 'Access denied.'})
      return self.response
    # TODO: if config.no_cors:
    self.response.headers.set('Access-Control-Allow-Origin', '*')
    try:
      response = self.action(request, self.response, {})
    except BaseException as e:
      traceback.print_exception(e)
      self.app.log("ERROR:", e)
      response = {"error": str(e)}
      self.response.status = 500
    if response.__class__ == list:
      self.response.response = json.dumps(response)
    elif response.__class__ == dict:
      self.response.response = json.dumps(response)
    elif response.__class__ == str:
      self.response.response = response

    return self.response

class Server(object):
  def __init__(self, app, port=4567, auth_key=""):
    self.app = app
    self.server = None
    self.port = port
    self.auth_key = auth_key
    self.flask = Flask(__name__,
        static_folder='../static',
        static_url_path='',
    )
    self.name_re = re.compile('[^A-Za-z0-9]')
    self.routes = {}

  def init(self):
    self.apis = []
    for api_cls in api.APIS:
      new_inst = api_cls(self.app)
      self.apis.append(new_inst)

  def reload(self, app):
    rreload(api)
    self.app = app
    self.init()

  def start(self):
    self.flask.run(port=self.port, threaded=True) #, debug=True)

  def add(self, url, handler, methods=['POST'], **kwargs):
    name = kwargs['name'] if 'name' in kwargs else None
    if name is None:
      name = re.sub(self.name_re, '_', url)
    if name in self.routes:
      self.routes[name].update_action(handler)
    else:
      self.routes[name] = EndpointAction(self.app, url, handler, kwargs)
      self.flask.add_url_rule(url, name, self.routes[name], methods=methods)

def rreload(module, mlist=None):
    """Recursively reload modules."""
    is_first = False
    if mlist is None:
      is_first = True
      mlist = []
    if module in mlist:
      return
    if not "__file__" in dir(module) or (not "backend" in module.__file__ or "backend/env" in module.__file__):
      return
    mlist.insert(0, module)
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if type(attribute) is ModuleType:
            rreload(attribute, mlist)
    for mod in mlist:
      print(f"Reloading module: {mod}")
      importlib.reload(mod)
