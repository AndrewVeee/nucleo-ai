import time
from markdownify import markdownify
from app.lib import web

def get_opt(opts, key, default=None):
  return opts[key] if key in opts else default

def set_opt(to_dict, from_dict, key, req=None, new_key=None):
  val = get_opt(from_dict, key, req)
  if val is None:
    return
  to_dict[new_key if new_key else key] = val

class Tools:
  def __init__(self, app):
    self.app = app;
    server = app.server
    server.add('/api/tools/markdown', self.markdown)
    server.add('/api/tools/url_to_md', self.url_to_md)

  def url_to_md(self, request, res, user):
    req = web.URLRetriever()
    self.app.debug(f"md: Retrieve url: {request.json['url']}")
    req.get_url(request.json['url'])
    self.app.debug(f"md: Convert to MD: {request.json['url']}")
    md = req.get_markdown()
    self.app.debug(f"md: Done: {request.json['url']}")
    return {
      'title': req.title,
      'content': md,
    }

  def markdown(self, request, res, user):
    return {
      'content': markdownify(request.json['content'])
    }
