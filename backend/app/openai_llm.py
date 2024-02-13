from openai import OpenAI

class OpenAILLM:
  def __init__(self, host, key, context_size=2048, model='untitled'):
    self.host = host
    self.key = key
    self.model = model
    self.context_size = context_size
    self.client = OpenAI(
      api_key=key,
      base_url=host
    )

  def chat_stream(self, messages, stream_args={}):
    stream = self.client.chat.completions.create(
      model=self.model,
      messages=messages,
      stream=True,
      **stream_args
    )

    for chunk in stream:
      if chunk.choices[0].delta.content is not None:
        yield chunk.choices[0].delta.content
