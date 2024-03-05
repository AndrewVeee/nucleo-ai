import time
import importlib

print(time.ctime(), "* Loading modules")
from app import \
  web_server, \
  sqlite, \
  config, \
  app_models, \
  functions, \
  openai_llm, \
  embed, \
  chroma
#  jwt, \

from ai_tools import prompt_loader
from app.lib import job_queue

class App:

  def __init__(self):
    self.log_level = 2
    self.log("* Loading config")
    self.config = config.Config(self)
    self._debug = True
    self.log_level = int(self.config.get('log_level', 1))
    
    self.log("* Initializing database")
    self.db = sqlite.Database(self)
    
    self.log("* Initializing RAG")
    self.embed = embed.RAG(self, config=self.config.get('embed', default={}))
    self.vector = chroma.VectorDB(self, config=self.config.get('embed', default={}))
    
    self.log("* Initializing webserver")
    self.server = web_server.Server(self,
      host=self.config.get('server_host', '127.0.0.1'),
      port=int(self.config.get('server_port', '4567')),
      auth_key=self.config.get('auth_key', ''), 
    )
    self.server.init()

    self.prompts = prompt_loader.PromptLoader(cache=self.config.get('cache_prompts', False))
    
    self.log("* Loading LLM")
    self.llm = openai_llm.OpenAILLM(
      self.config.get('openai_base_url', path="llm"),
      self.config.get('openai_api_key', path="llm"),
      model=self.config.get('openai_model', 'untitled', path="llm"),
      context_size=self.config.get('context_size', 2048, path="llm"),
    )
    self.log(f"  {self.llm.host} [key len={len(self.llm.key)}] [model={self.llm.model}]")

    self.log("* Starting job queue")
    self.llm_queue = job_queue.JobQueue(
      runners=int(self.config.get('max_concurrent', 1, path='llm'))
    )

    self.log("* Loading functions")
    self.ai_functions = functions.Functions
    functions.init(self)
    for entry in self.ai_functions.entries:
      self.log((
        f"  {entry.title}: "
        f"{entry.get_description()}"
        f" - {[fn.name for fn in entry.functions]}"
      ))

    self.log("* Loading Models")
    self.ai_models = app_models.AppModels(self)
    self.log(f"  Models: {[model.name for model in self.ai_models.model_list]}")

#    self.log("* Initializing VectorDB")
#    self.vector = chroma.VectorDB(self)
    self.reload_count = 0
#    self.jwt = jwt.JWT(self.app_secret)
    
  def reload(self, opts=['config', 'api']):
    self.reload_count += 1
    if 'config' in opts:
      importlib.reload(config)
      self.config = config.Config(self)

    if 'api' in opts:
      self.server.reload(self)

  def start(self):
    self.log("* Starting!")
    self.server.start()

  def log(self, *args, level=2):
    if self.log_level >= level:
      print(f"[{time.ctime()}]", *args)

  def debug(self, *args):
    self.log(*args, level=3)
    #if self._debug:
    #  print(time.ctime(), "DEBUG:", *args)

  def get_storage_dir(self, name, ex="", file=""):
    pass

if __name__ == '__main__':
  App().start()
