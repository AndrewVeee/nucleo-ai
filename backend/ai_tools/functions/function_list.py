
def get_opt(args, name, value=None):
  return args[name] if name in args else value

class FunctionArg:
  def __init__(self, name, description, question, values,
      multiline=False, default=None, disabled=False, stream_response=False):
    self.name = name
    self.description = description
    self.question = question
    self.values = values
    self.multiline = multiline
    self.default = default
    self.stream_response = stream_response
    self.disabled = disabled
  
  def get_full_string(self):
    return (
      f"Name: {self.name}\nPurpose: {self.description}\n{self.question}"
    )
  def to_dict(self):
    return {
      'name': self.name, 'description': self.description,
      'question': self.question, 'values': self.values,
      'multiline': self.multiline, 'default': self.default,
    }

class NamedFunction:
  def __init__(self, handler, name, description, fn_list=None, short_description=None):
    self.handler = handler
    self.name = name
    self.description = description
    self.short_description = short_description
    self.arguments = []
    self.argument_map = {}
    self.fn_list = fn_list

  def single_line_args(self):
    args = []
    for arg in self.arguments:
      if arg.multiline == False:
        args.append(arg)
    return args

  def simple_args_string(self):
    arg_str =""
    for arg in self.arguments:
      if arg.multiline == False:
        arg_str += f"{arg.name}: {arg.description}"
        if arg.default != None:
          arg_str += f" (Default: {arg.default})"
        arg_str += "\n"
    return arg_str.strip()

  def argument_list(self):
    arg_list = []
    for arg in self.arguments:
      if arg.disabled != True:
        arg_list.append(arg.to_dict())
    return arg_list

  def get_description(self):
    return f"{self.name}: {self.description}"

  def add_argument(self, name, description, question, multiline=False, values=None, default=None, disabled=False,
    stream_response=False
  ):
    new_arg = FunctionArg(name, description, question, values,
        multiline=multiline,
        default=None,
        disabled=disabled,
        stream_response=stream_response,
    )
    self.arguments.append(new_arg)
    self.argument_map[new_arg.name] = new_arg
    return self

  def add_to(self, title):
    self.fn_list.entry_map[title].add_fn(self)
    return self

class FunctionEntry:
  def __init__(self, title, alias, description, examples=[]):
    self.title = title
    self.alias = alias
    self.description = description
    self.examples = examples
    self.fn_descriptions = []
    self.functions = []
    self.function_map = {}
  
  def get_functions_string(self):
    return "\n".join([
      fn.get_description()
      for fn in self.functions
    ])
  def get_description(self):
    return ', '.join(self.fn_descriptions)
    
  def add_fn(self, fn):
    self.functions.append(fn)
    self.function_map[fn.name] = fn
    if fn.short_description is not None and fn.short_description not in self.fn_descriptions:
      self.fn_descriptions.append(fn.short_description)

class FunctionList:
  def __init__(self, **kwargs):
    self.title = get_opt(kwargs, 'title')
    self.description = get_opt(kwargs, 'description')
    self.use_aliases = get_opt(kwargs, 'use_aliases', True)
    self.all_functions = []
    self.entries = []
    self.entry_map = {}
    self.aliases = ['Alex', 'Jamie', 'Jordan', 'Madison', 'Riley', 'Jayden', 'Lindsey', 'Rowan', 'Sloan', 'Blythe']
    self.alias_idx = 0

  def example_string(self):
    examples = ""
    ex_idx = 1
    for entry in self.entries:
      assistant = entry.alias if self.use_aliases else entry.name
      for example in entry.examples:
        if examples != "":
          examples += "\n"
        examples += f"{ex_idx}. {assistant}: {example}"
        ex_idx += 1
    return examples

  def all_functions_string(self):
    fns = ""
    for entry in self.entries:
      fns += entry.get_functions_string() + "\n"
    return fns.strip()

  def entry_list_string(self):
    def entry_name(entry):
      return entry.alias if self.use_aliases else entry.title

    return "\n".join([
      f"{entry_name(entry)}: Handles {entry.get_description()}"
      for entry in self.entries
    ])

  def get_entry(self, name):
    for entry in self.entries:
      if entry.alias == name or entry.title == name:
        return entry

  def get_next_alias(self):
    alias = self.aliases[self.alias_idx]
    self.alias_idx += 1
    return alias

  def add_entry(self, title, description, auto_fail=False, examples=[]):
    entry = FunctionEntry(title, self.get_next_alias(), description, examples=examples)
    self.entries.append(entry)
    self.entry_map[title] = entry
    return entry
  
  def define(self, handler, name, description, short_description=None):
    new_fn = NamedFunction(handler, name, description, self, short_description=short_description)
    self.all_functions.append(new_fn)
    return new_fn
