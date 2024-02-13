import re

from .prompt import Prompt
from .entry import ChainPromptEntry

def get_opt(opts, name, default=None):
  return opts[name] if name in opts else default

def parse_list(output, parse_opt):
  list_re = re.compile(r"^(\d+. |\- |.* \d(\:|\.) )(.*)")
  out_list = []
  for line in output.split("\n"):
    match = list_re.fullmatch(line)
    if match is not None:
      out_list.append(match[3])
  return out_list

def parse_log_message(output, parse_opt):
  return parse_opt

def parse_full_response(output, parse_opt):
  return output

def parse_from_line(output, parse_opt):
  for line in output.split("\n"):
    if line.lower().startswith(parse_opt.lower()):
      return line[len(parse_opt):].strip()
  return ''

class ChainInstance:
  def __init__(self, chain, **kwargs):
    self.chain = chain
    self.opts = get_opt(kwargs, 'opts', {}) 
    self.state = get_opt(kwargs, 'state', {})
    self.run_list = []
    for root in self.chain.roots:
      self.run_list.append(root)
    self.event_handler = get_opt(kwargs, 'handler')
    self.runner = get_opt(kwargs, 'runner')
    self.stopped = False
    self.parser_fns = {
      'full_response': parse_full_response,
      'from_line': parse_from_line,
      'list': parse_list,
      'log_message': parse_log_message,
    }
 
  def runner(self):
    print(f"*** No runner provided.")
    return "Fake response\nBlah: 1"

  def set_opt(self, name, value):
    self.opts[name] = value
  def get_opt(self, name, default=None):
    return self.opts[name] if name in self.opts else default
  
  def send_event(self, name, data):
    if self.event_handler:
      self.event_handler(name, {
        'data': data,
        'state': self.state,
      }, self)

  def stop(self):
    self.run_list = []
    self.stopped = True

  def run_next(self):
    if len(self.run_list) == 0:
      return None
    entry = self.run_list.pop(0)
    self.send_event('start_entry', {'value': entry.name, 'entry': entry})
    if self.stopped:
      return None
    result = entry.run(self)
    if result['success']:
      for child in reversed(result['children']):
        self.run_list.insert(0, child)
    return result

class PromptChain:
  def __init__(self):
    self.roots = []

  def create_instance(self, state, **kwargs):
    return ChainInstance(self, state=state, **kwargs)

  def add_entry(self, entry):
    self.roots.append(entry)
    return entry

  def add_prompt_entry(self, name='untitled'):
    new_entry = ChainPromptEntry(name=name, entry_type='prompt', chain=self)
    self.roots.append(new_entry)
    return new_entry
