from app.lib import stream_queue

class AIModels:
  def __init__(self):
    self.models = []
    self.model_map = {}
    self.default = None

  def add_model(self, model, default=False):
    self.models.append(model)
    self.model_map[model.name] = model
    if default:
      self.default = model
  
  def get_model(self, name):
    if name in self.model_map:
      return self.model_map[name]
    return self.default

class AIBaseModel:
  def __init__(self, name, llm, app):
    self.llm = llm
    self.name = name
    self.app = app

  def create_thread_queue(self, default="", cfg={}):
    return stream_queue.QueueThread(default=default)

  def generate_block(self, content, assistant=None):
    delta = {"content": content}
    block = {
      "id":1,"object":"chat.completion.chunk",
      "choices":[{"index":0,"delta": delta}],
      "created":1694268190,
      "model":"none",
      "system_fingerprint":"123",
      "logprobs":None,
      "finish_reason":None
    }
    if assistant:
      delta['function_call'] = {'name': 'assistant', 'arguments': assistant}
    return block

  def get_opt(self, opts, name, default=None):
    return opts[name] if name in opts else default
  
  def default_opts(self, opts):
    return {
      'temperature': self.get_opt(opts, 'temperature', 0)
    }

class ChainRunner:
  def __init__(self, chain, llm, handler, state, app):
    self.llm = llm
    self.handler = handler
    self.app = app

    self.instance = chain.create_instance(
      state,
      handler=self.on_event,
      runner=self.run_llm_job,
    )

  def run_llm_job(self, messages, entry):
    job = self.app.llm_queue.add(self.run_llm, {
      'entry': entry,
      'messages': messages,
    })
    job.wait()
    if job.exception:
      raise job.exception
    return job.result

  def run_llm(self, opts):
    res = ''
    stream_args = {
      'temperature': opts['entry'].get_opt('temperature', 0)
    }
    for chunk in self.llm.chat_stream(opts['messages'], stream_args):
      self.handler('response', chunk, opts['entry'], self.instance)
      res += chunk
    self.handler('response_end', '', opts['entry'], self.instance)
    return res

  def run_llm_old(self, messages, entry):
    res = ''
    temp = entry.get_opt('temperature', 0)
    for chunk in self.llm.chat_stream(messages):
      self.handler('response', chunk, entry, self.instance)
      res += chunk
    return res

  def on_event(self, event, data, instance):
    self.handler(event, data, None, instance)

  def run(self):
    while True:
      res = self.instance.run_next()
      if res is None:
        break