from .prompt import Prompt

class ChainEntryBase:
  def __init__(self, entry_type='custom', name='untitled', chain=None, **kwargs):
    self.type = entry_type
    self.name = name
    self.entry = None
    self.children = []
    self.conditions = []
    self.events = []
    self.parsers = []
    self.opts = {}
    self.chain = chain

  def get_opt(self, name, default=None):
    return self.opts[name] if name in self.opts else default #get_opt(self.opts, name, default)
  def set_opt(self, name, value):
    self.opts[name] = value

  def parser(self, parser_name, output_name, parser_opts='', event=None):
    self.parsers.append({
      'parser': parser_name,
      'opts': parser_opts,
      'output': output_name,
      'event': event,
    })
    return self

  def add_event(self, event_name, send_value, send_type="state", before_run=False):
    self.events.append({
      'name': event_name,
      'type': send_type,
      'value': send_value,
      'before_run': before_run,
    })

  def condition(self, state_name, operator, value):
    self.conditions.append({
      'name': state_name,
      'op': operator,
      'value': value,
    })
    return self
  
  def check_condition(self, cond, state):
    key = cond['name']
    state_value = state[key].lower() if key in state else ''
    cond_value = cond['value'].lower()
    if cond['op'] == 'includes':
      return state_value.find(cond_value) != -1
    if cond['op'] == 'eq':
      return state_value == cond_value
    if cond['op'] == 'ne':
      return state_value != cond_value
    if cond['op'] == 'exclude':
      return state_value.find(cond_value) == -1
      
    return True
  
  def parse_results(self, output, instance):
    for parser in self.parsers:
      p_name = parser['parser']
      if p_name in instance.parser_fns:
        result = instance.parser_fns[p_name](output, parser['opts'])
        instance.state[parser['output']] = result
        if parser['event']:
          instance.send_event(parser['event'], {'value': result, 'inst': instance})
      else:
        # Error: parser not found
        pass

  def add_entry(self, entry):
    self.children.append(entry)
    return entry

  def add_prompt_entry(self, name='untitled'):
    new_entry = ChainPromptEntry(name=name, entry_type='prompt', chain=self.chain)
    self.children.append(new_entry)
    return new_entry

  def send_events(self, instance, before_run=False):
    for event in self.events:
      # Only send events for before/after run.
      if event['before_run'] == True and before_run == False or \
          event['before_run'] == False and before_run == True:
        continue
    
      if event['type'] == 'state':
        value = instance.state[event['value']] if event['value'] in instance.state else None
      else:
        value = event['value']
      instance.send_event(event['name'], {'value': value})
  
  def run(self, instance):
    for cond in self.conditions:
      if not self.check_condition(cond, instance.state):
        instance.send_event('skip', {'cond': cond})
        return {'skipped': True, 'success': True, 'children': []}
    self.send_events(instance, before_run=True)
    result = self.runner(instance)
    if 'response' in result:
      self.parse_results(result['response'], instance)
    children = result['children'] if 'children' in result else self.children
    self.send_events(instance, before_run=False)
    return {
      'success': True,
      #'children': self.children,
      'children': children
    }

class ChainFunctionEntry(ChainEntryBase):
  def __init__(self, fn, opts=None, entry_type='functionentry', *args, **kwargs):
    self.fn = fn
    self.opts = opts
    super().__init__(*args, **kwargs)

  def runner(self, instance):
    response = {
      'response': None,
      'children': self.children,
    }
    self.fn(instance, response, self.opts)
    return response


class ChainStateSetter(ChainEntryBase):
  def __init__(self, state_name, state_value='', setter=None, entry_type='statesetter', *args, **kwargs):
    self.state_name = state_name
    self.state_value = state_value
    self.setter = setter
    super().__init__(*args, **kwargs)

  def runner(self, instance):
    value = self.state_value
    if self.setter is not None:
      value = self.setter()
    instance.state[self.state_name] = value
    instance.send_event("StateSetter:set", {'value': f"{self.state_name} -> {self.state_value}", 'inst': instance})
    return {'response': None, 'children': self.children}
  
# Runs each child entry for every item in the state variable 'state_name'
class ChainForEachEntry(ChainEntryBase):
  def __init__(self, state_name, entry_type='foreach', *args, **kwargs):
    self.state_name = state_name
    self.entry_loop = []
    super().__init__(*args, **kwargs)

  def add_loop_entry(self, entry):
    self.entry_loop.append(entry)
    return entry

  def runner(self, instance):
    state_list = instance.state[self.state_name]
    if state_list.__class__ == str:
      state_list = parse_list(state_list, '')
    
    children = []
    for result in state_list:
      # For each result, add a state setter and add all entry_loop entries to it.
      state_setter = ChainStateSetter(f"{self.state_name}_entry", result, chain=self.chain)
      children.append(state_setter)
      for child in self.entry_loop:
        state_setter.add_entry(child)
    # After loop entries are run, add regular child entries.
    for child in self.children:
      children.append(child)
    return {'response': None, 'children': children}
 
class ChainPromptEntry(ChainEntryBase):
  def __init__(self, entry_type='prompt', *args, **kwargs):
    super().__init__(self, *args, **kwargs)
    self.entry = None
    self.type = entry_type
    self.stream_state = kwargs.get('stream_state', None)
    if entry_type == 'prompt':
      self.entry = Prompt()
  
  def add_message(self, *args, **kwargs):
    self.entry.add_message(*args, **kwargs)

  def add_prompt_entry(self, name='untitled'):
    new_entry = ChainPromptEntry(name=name, entry_type='prompt', chain=self.chain)
    self.children.append(new_entry)
    return new_entry

  def parser(self, parser_name, output_name, parser_opts='', event=None):
    self.parsers.append({
      'parser': parser_name,
      'opts': parser_opts,
      'output': output_name,
      'event': event,
    })
  def condition(self, state_name, operator, value):
    self.conditions.append({
      'name': state_name,
      'op': operator,
      'value': value,
    })
  
  def check_condition(self, cond, state):
    key = cond['name']
    state_value = state[key].lower() if key in state else ''
    cond_value = cond['value'].lower()
    if cond['op'] == 'includes':
      return state_value.find(cond_value) != -1
    if cond['op'] == 'eq':
      return state_value == cond_value
    if cond['op'] == 'ne':
      return state_value != cond_value
    if cond['op'] == 'exclude':
      return state_value.find(cond_value) == -1
      
    return True
  
  def run_prompt(self, instance):
    messages = self.entry.inst_fill(instance.state)
    return instance.runner(messages, self)

  def parse_results(self, output, instance):
    for parser in self.parsers:
      p_name = parser['parser']
      if p_name in instance.parser_fns:
        result = instance.parser_fns[p_name](output, parser['opts'])
        instance.state[parser['output']] = result
        if parser['event']:
          instance.send_event(parser['event'], {'value': result, 'inst': instance})
      else:
        # Error: parser not found
        pass

  def runner(self, instance):
    for cond in self.conditions:
      if not self.check_condition(cond, instance.state):
        instance.send_event('skip', {'cond': cond})
        return {'skipped': True, 'success': True, 'children': []}
    return {'response': self.run_prompt(instance)}
 