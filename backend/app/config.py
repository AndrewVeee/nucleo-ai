import tomllib

class Config:
  def __init__(self, app):
    self.app = app
    self.user_conf = self.load_toml('../data/config.toml')
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
    try:
      with open(file, 'rb') as f:
        cfg = tomllib.load(f)
    except:
      self.app.log(f"ERROR: Unable to load config file: {file}")
      cfg = {}

    return cfg
