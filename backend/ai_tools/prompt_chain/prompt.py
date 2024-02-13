def get_opt(opts, name, default=None):
  return opts[name] if name in opts else default

class Message:
  def __init__(self, **kwargs):
    self.role = get_opt(kwargs, 'role', 'user')
    self.message = get_opt(kwargs, 'message', '')
    self.state = get_opt(kwargs, 'state', {})

  def fill(self, state=None):
    if state is None:
      state = self.state
    
    msg = self.message
    for key in state.keys():
      if state[key].__class__ == list:
        msg = msg.replace('{{' + str(key) + '}}', "\n".join(state[key]))
      else:
        msg = msg.replace('{{' + str(key) + '}}', str(state[key]))
    return msg

class PromptInstance:
  def __init__(self, prompt, state={}):
    self.state = state
    self.prompt = prompt

  def fill(self, state):
    messages = []
    for msg in self.prompt.messages:
      messages.append({
        'role': msg.role,
        'content': msg.fill(state=state)
      })
    return messages

class Prompt:
  def __init__(self):
    self.messages = []
  
  def add_message(self, message, role='user'):
    self.messages.append(Message(message=message, role=role))
  
  def inst_fill(self, state):
    return PromptInstance(prompt=self).fill(state)

  def instance(self, state={}):
    return PromptInstance(prompt=self, state=state)
