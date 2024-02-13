class PromptLoader:
  def __init__(self, path='./prompts', ext="", cache=True):
    self.path = path
    self.store_cache = cache
    self.ext = ext
    self.cache = {}

  def get(self, name):
    if name in self.cache:
      return self.cache[name]

    with open(f"{self.path}/{name}{self.ext}", 'r') as file:
      contents = file.read().strip()

    if self.store_cache:
      self.cache[name] = contents
    return contents
