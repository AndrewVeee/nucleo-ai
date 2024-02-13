import json

class Chat:
  def __init__(self, app):
    self.app = app;
    server = app.server
    server.add('/api/v1/chat/completionsx', self.chat)
    server.add('/api/v1/chat/completions', self.chat_model)
    server.add('/v1/api/rag-completions', self.rag_chat)

  def chat_wrapper(self, fn, messages):
    for chunk in fn(messages):
      line = "data: " + \
        json.dumps(self.generate_block(chunk)) + \
        "\n\n"
      yield line

  def rag_wrapper(self, query):
    rag_results = self.app.embed.search.query(1, query)
    rag_str = ''

    if len(rag_results) > 0:
      rag_str = "\n\nHere is some context that may help answer:\n" + \
        "\n".join([
          f"```{res.store_id}\n{res.chunk}\n```"
          for res in rag_results
        ])
    messages = [
      {
        'role': 'system',
        'content': f"You are an expert AI assistant. Try to answer the user below." + rag_str
      },
      { 'role': 'user', 'content': query }
    ]
    yield f"data: {json.dumps({'prompt':messages})}\n"
    yield f"data: {json.dumps({'rag':[res.to_dict() for res in rag_results]})}\n"
    for chunk in self.app.llm.chat_stream(messages):
      line = "data: " + \
        json.dumps({'choices': [{'content': chunk}]}) + \
        "\n"
      yield line

  def rag_chat(self, req, res, user):
    query = req.json['query']
    res.response = self.rag_wrapper(query)

  def queue_model_wrapper(self, model, messages, **kwargs):
    tq = model.create_thread_queue()
    self.app.main_job_queue.add(model.run_as_job, {
      'messages': messages,
      'tq': tq,
      'kwargs': kwargs,
    })
    for chunk in tq.queue:
      if chunk != "":
        yield "data: " + json.dumps(chunk) + "\n\n"

  def model_wrapper(self, fn, messages, **kwargs):
    for chunk in fn(messages, cfg={'app': self.app}, **kwargs):
      if chunk != "":
        yield "data: " + json.dumps(chunk) + "\n\n"
    #print("Wrapper end")

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
    #print(f"Chat Wrapper Completed")

  def chat(self, req, res, user):
    messages = req.json['messages']
    res.response = self.chat_wrapper(self.app.llm.chat_stream, messages) #self.app.llm.chat_stream(messages)
