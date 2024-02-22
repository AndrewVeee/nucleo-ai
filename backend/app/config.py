import toml

class Config:
  def __init__(self, app):
    self.app = app
    try:
      self.user_conf = self.load_toml('../data/config.toml')
    except Exception as e:
      self.app.log("ERROR: Unable to load config file: {file}")
      raise e
    self.config = {}
    self.config.update(self.user_conf)

  def get(self, name, default=None, path=None):
    cfg = self.config
    if path:
      for part in path.split("."):
        if part in cfg:
          cfg = cfg[part]
        else:
          return default
    if name in cfg:
      return cfg[name]
    return default
  
  def load_toml(self, file):
    return toml.load(file)
