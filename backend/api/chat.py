import json

class Chat:
  def __init__(self, app):
    self.app = app;
    server = app.server
    server.add('/api/v1/chat/completions', self.chat_model)

  def model_wrapper(self, fn, messages, **kwargs):
    for chunk in fn(messages, cfg={'app': self.app}, **kwargs):
      if chunk != "":
        yield "data: " + json.dumps(chunk) + "\n\n"
    self.app.log("Request completed.", level=3)

  def chat_model(self, req, res, user):
    messages = req.json['messages']
    model = req.json['model']
    req_config = {}
    for idx,msg in enumerate(messages):
      if msg['role'] == 'config':
        messages.pop(idx)
        try:
          req_config = json.loads(msg['content'])
        except:
          pass
        break

    ai_model = self.app.ai_models.get_model(model)
    self.app.log(f"Using model: {ai_model.name} ({req_config})", level=2)
    res.response = self.model_wrapper(ai_model.run, request_config=req_config, **req.json)
