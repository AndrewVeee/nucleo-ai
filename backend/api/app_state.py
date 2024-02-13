import time

class AppState:
  def __init__(self, app):
    self.app = app;
    server = app.server
    server.add('/', self.home, methods=['GET'], auth=False)
    server.add('/api/state/check_auth', self.test_conn)
    server.add('/state/api', self.list_apis)
    server.add('/state/config', self.get_config)
    server.add('/state/test_stream', self.test_stream)
    server.add('/state/reload', self.reload)

  def test_stream(self):
    for i in range(5):
      yield f"Test {i}"
      time.sleep(1)

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

  def test_stream(self, req, res, user):
    res.headers.set('Content-Type', 'application/stream')
    res.response = self.test_stream()

  def get_config(self, req, res, user):
    return {"reload_cnt": self.app.reload_count, "config": self.app.config.config}
