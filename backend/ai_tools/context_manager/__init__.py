from enum import Enum
import time

Roles = Enum('Role', ['user', 'system', 'assistant'])

class CtxMessage:
  def __init__(self, message, role=Roles.user, **kwargs):
    self.message = message
    self.role = role
    self.time = kwargs['time'] if 'time' in kwargs else time.time()

# Don't use a ranker
class NoRanker:
  def __init__(self):
    pass

  def rank(self, text, content_list):
    ranks = []
    for i in range(len(content_list)):
      ranks.append(1)
    return ranks

# Simple ranking based on word occurrences
class SimpleRanker:
  def __init__(self):
    pass

  def rank(self, text, content_list):
    ranks = []
    words = text.lower().split(" ")
    words = [word.rstrip('?!.:;\t\n') for word in words]
    highest = 0.1
    for entry in content_list:
      score = 0
      entry_lc = entry.lower()
      for word in words:
        if word in entry_lc:
          score += 1
      if highest < score:
        highest = score
      ranks.append(score)
    
    for i in range(len(ranks)):
      ranks[i] = ranks[i] / highest * 10
    return ranks

# Context manager to generate AI chat messages.
class ContextManager:
  def __init__(self, **kwargs):

    # Message history + dynamic content for each request
    self.messages = []
    self.dynamic = {}
    
    # Content specific to each message
    self.ephemeral = []
    self.requests = []
    self.request_text = ''

    # Max context size
    self.max_tokens = self.get_opt(kwargs, 'max_tokens', 1024)
    # Function to count tokens
    self.token_counter = self.get_opt(kwargs, 'token_counter', self.count_tokens)
    # Function to rank items
    self.ranker = self.get_opt(kwargs, 'ranker', NoRanker().rank)
    # Number of past messages to try to include in context
    self.last_messages = self.get_opt(kwargs, 'last_messages', 4)

    # Allow overriding role names
    self.role_map = {
      Roles.user: 'user',
      Roles.system: 'system',
      Roles.assistant: 'assistant'
    }

    # Starting scores to prioritize what should be included in history
    # Scores 0 and lower will be dropped
    self.dynamic_score = 0 # Dynamic data can be dropped
    self.ephemeral_score = 1 # Ephemeral data related to the current task should be included if possible
    self.message_score = 0 # Chat history is slightly more important than ephemeral data

  def get_opt(self, opts, name, default=None):
    if name in opts:
      return opts[name]
    return default

  # Generic token counter if none provided.
  def count_tokens(self, content):
    return int(len(content) / 3)

  def start_new_message(self):
    self.ephemeral = []
    self.requests = []
    self.request_text = ''

  def request(self, content, role=Roles.user, include_text=True):
    request = {
      'content': content,
      'role': role
    }
    if include_text:
      self.request_text += "\n" + content
    self.requests.append(request)
    return request

  def add_message(self, content, role=Roles.user, **kwargs):
    msg = CtxMessage(content, role, **kwargs)
    self.messages.append(msg)
    return msg

  def add_ephemeral(self, content, **kwargs):
    ephem = {
      'content': content,
      'role': kwargs.get('role', Roles.system)
    }
    self.ephemeral.append(ephem)
    return ephem

  def add_dynamic(self, name, title, fn=None, content=""):
    self.dynamic[name] = {
      "name": name,
      "title": title,
      "fn": fn,
      "content": content
    }
    return self.dynamic[name]

  def gen_message_map(self):
    all_messages = []
    msg_map = {}
    idx = 0
    for dyn_key in self.dynamic.keys():
      all_messages.append(self.dynamic[dyn_key]['title'])
      msg_map[idx] = {'type': 'dyn', 'obj': self.dynamic[dyn_key], 'score': self.dynamic_score, 'include': False}
      idx += 1
    for ephem in self.ephemeral:
      all_messages.append(ephem['content'])
      msg_map[idx] = {'type': 'ephemeral', 'obj': ephem, 'score': self.ephemeral_score, 'include': False}
      idx += 1
    for msg in self.messages:
      all_messages.append(msg.message)
      msg_map[idx] = {"type": 'msg','obj': msg, 'score': self.message_score, 'include': False}
      idx += 1
    
    return [all_messages, msg_map]

  def get_item_content(self, item):
    if item['type'] == 'dyn':
      if item['obj']['fn']:
        return item['obj']['fn']()
      else:
        return item['obj']['content']
    elif item['type'] == 'ephemeral':
      return item['obj']['content']
    elif item['type'] == 'msg':
      return item['obj'].message
    return None

  def generate_message_list(self, sorted_map, past_messages):
    messages = []
    # TODO: Keep message history in order
    for item in sorted_map:
      if not item['include']:
        continue
      if item['type'] == 'msg':
        role = item['obj'].role
        msg = item['obj'].message
      elif item['type'] == 'dyn':
        role = Roles.system
        msg = item['content']
      elif item['type'] == 'ephemeral':
        role = item['obj']['role'] #Roles.system
        msg = item['obj']['content']
      messages.append({'role': self.role_map[role], 'content': msg})
    for msg in past_messages:
      messages.append({'role': self.role_map[msg.role] if msg.role in self.role_map else msg.role, 'content': msg.message})
    for req in self.requests:
      #messages.append({'role': self.role_map[req['role']], 'content': req['content']})
      messages.append({'role': self.role_map[req['role']] if req['role'] in self.role_map else req['role'], 'content': req['content']})
    return messages

  def generate_messages(self):
    req = self.requests[-1]
    token_count = 0

    # Generate a list with all content and a map of each index to it's type/obj
    msg_content, msg_map = self.gen_message_map()
    # Rank the content and apply the scores
    if len(msg_content) == 0:
      scores = []
    else:
      scores = self.ranker(self.request_text, msg_content)
    for idx,score in enumerate(scores):
      msg_map[idx]['score'] += score
    
    # Set initial token count to requests content
    for req in self.requests:
      token_count += self.token_counter(req['content'])

    # Include previous messages up to last_messages if they fit in the context
    last_messages = []
    for i in range(self.last_messages):
      if i + 1 > len(self.messages):
        break
      msg = self.messages[-i]
      msg_tokens = self.token_counter(msg.message)
      if token_count + msg_tokens <= self.max_tokens:
        token_count += msg_tokens
        last_messages.append(msg)

    # Sort map by score and determine which items can be included
    sorted_map = sorted(msg_map, key=lambda msg_idx: msg_map[msg_idx]['score'], reverse=True)  
    sorted_map = [msg_map[idx] for idx in sorted_map]

    # Decide which other items to include. Based on score, up to max_tokens.
    for item in sorted_map:
      if item['obj'] in last_messages:
        continue
      content = self.get_item_content(item)
      tokens = self.token_counter(content)
      if token_count + tokens <= self.max_tokens:
        # Don't include items with a score <= 0
        if item['score'] <= 0:
          break
        # We're adding the item, so if it's dynamic, set the content so we don't call the fn again.
        if item['type'] == 'dyn':
          item['content'] = content
        token_count += tokens
        item['include'] = True

    # Generate the full message list
    return self.generate_message_list(sorted_map, last_messages)
