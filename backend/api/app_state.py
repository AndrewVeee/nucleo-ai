from flask import send_from_directory

import os
import time

class AppState:
  def __init__(self, app):
    self.app = app;
    server = app.server
    server.add('/', self.home, methods=['GET'], auth=False)
    server.add('/uploads/<file>', self.serve_upload, methods=['GET'])
    server.add('/api/state/check_auth', self.test_conn)
    server.add('/state/api', self.list_apis)
    server.add('/state/config', self.get_config)
    server.add('/state/reload', self.reload)

  def serve_upload(self, req, res, user):
    filename = req.path[9:]
    return send_from_directory("../../data/uploads", filename)

  def home(self, req, res, user):
    res.status = 302
    res.headers.set('Location', '/index.html')

  def test_conn(self, req, res, user):
    return {
      'status': 'Ready!'
    }

  def list_apis(self, req, res, user):
    routes = []
    for route_key in self.app.server.routes:
      route = self.app.server.routes[route_key]
      routes.append({
        "url": route.url,
        "opts": route.opts,
      })
    return {"routes": routes}

    
  def reload(self, req, res, user):
    self.app.reload()
    return self.get_config(req, res, user)

  def get_config(self, req, res, user):
    return {"reload_cnt": self.app.reload_count, "config": self.app.config.config}
