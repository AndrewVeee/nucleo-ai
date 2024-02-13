from .ai_model_base import AIBaseModel, ChainRunner
from ai_tools import prompt_chain as pc
from app.lib.string_tools import fill_prompt

import re

class AssistantEntry(pc.entry.ChainEntryBase):
  def __init__(self, *args, **kwargs):
    super().__init__(self, *args, **kwargs)

  def get_assistant(self, app, task):
    for entry in app.ai_functions.entries:
      if entry.alias.lower() in task.lower():
        return entry
    return None

  def runner(self, instance):
    app = instance.get_opt('cfg')['app']
    task = instance.state['task']
    assistant = self.get_assistant(app, instance.state['task'])

    if not assistant:
      instance.state['errors'].append(f"No assistant found for {task}")
    # Set the assistant for this chain and tool list.
    instance.set_opt('assistant', assistant)
    instance.state['tool_list'] = assistant.get_functions_string()
    instance.send_event('status', {'value': [assistant.title, instance.state['tool_list']]})
    return {'response': None, 'children': self.children}

class GetFunctionEntry(pc.entry.ChainEntryBase):
  def __init__(self, *args, **kwargs):
    super().__init__(self, *args, **kwargs)

  def get_fn(self, app, task):
    for entry in app.ai_functions.entries:
      if entry.alias.lower() in task.lower():
        return entry
    return None

  def runner(self, instance):
    assistant = instance.get_opt('assistant')
    sel_fn = None
    for fn in assistant.functions:
      if fn.name in instance.state['function']:
        sel_fn = fn
        break
    if sel_fn is not None:
      instance.state['found_fn'] = 'yes'
      instance.set_opt('function', sel_fn)
      instance.state['simple_args'] = sel_fn.simple_args_string()
      instance.state['multiline_args'] = [fn.name for fn in sel_fn.arguments if fn.multiline == True]
      #instance.state['args'] = fn.arg_list
      instance.send_event('status', {'value': ["call_fn", fn.name, instance.state['simple_args'], instance.state['multiline_args']]})
    else:
      instance.state['found_fn'] = 'no'

    return {'response': None, 'children': self.children}

def create_function_chain(app):
  # Function Call chain.
  # Need to set the following state:
  # - task: Current task to run
  # - task_list: List of tasks for context
  # - message: Original message for context
  # - request_ctx: List to add context data (search results, etc)
  # Additionally, use set_opt('cfg', {'app': app}) on the instance
  chain = pc.PromptChain()
  set_assistant = chain.add_entry(AssistantEntry())
  # set_assistant sets tool_list
  choose_fn = set_assistant.add_prompt_entry('choose-fn')
  choose_fn.add_message(app.prompts.get('functions/choose-fn-sys'))
  choose_fn.add_message("{{task}}")
  choose_fn.parser('from_line', 'function', parser_opts='tool:')
  get_fn = choose_fn.add_entry(GetFunctionEntry(name="Get Function", chain=chain))
  get_simple_args = get_fn.add_prompt_entry("Get single line args")
  get_simple_args.condition('found_fn', 'eq', 'yes')
  get_simple_args.add_message(app.prompts.get('functions/get-simple-args-sys'), "system")
  #get_simple_args.add_message("{{task}}")
  get_simple_args.parser('full_response', 'simple_arg_values')
  get_simple_args.add_event('status', 'simple_arg_values')
  get_multiline_args = choose_fn.add_entry(pc.entry.ChainForEachEntry(
    "multiline_args", name="multiline_args", chain=chain)
  )
  
  # For each multiline argument, this function is called to set state variables
  # that can be embedding in the prompt.
  def set_multiline_state(inst, res, opts):
    arg = inst.state[f"multiline_args_entry"]
    fn = inst.get_opt('function')
    inst.state['multiline_desc'] = fn.argument_map[arg].get_full_string()
    #print(f"*** Set multiline desc for {arg}:\n{inst.state['multiline_desc']}\n***")
  
  # After each multiline argument prompt, this is run to set the value.
  def set_multiline_arg(inst, res, opts):
    arg = inst.state["multiline_args_entry"]
    new_key = f"ml_arg_{arg}"
    inst.state[new_key] = inst.state['multiline_arg_value']
    #print(f"*** Set ml value: {[inst.state[new_key]]}")

  # Once all arguments have been prompted, this collects all of the arguments.
  simple_arg_re = re.compile(r'^([^:]+): (.*)$')
  def set_fn_args(inst, res, opts):
    args = {}
    for line in inst.state['simple_arg_values'].split("\n"):
      match = simple_arg_re.fullmatch(line)
      if match and match[1].lower() in inst.state['simple_args']:
        args[match[1]] = match[2].strip('"')
    for arg_name in inst.state['multiline_args']:
      args[arg_name] = inst.state[f"ml_arg_{arg_name}"]
    fn = inst.get_opt('function')
    inst.set_opt('function_arguments', args)
    print(f"*** Call Function: {fn.name} ({args})")

  def call_function(inst, res, opts):
    fn = inst.get_opt('function')
    if fn is None:
      task = inst.state['task']
      result = {
        'success': False,
        'result': f'Unable to perform task: {task}. No function found.',
        'response': f"I wasn't able to perform this task: {task}",
      }
    else:
      result = fn.handler(inst, inst.get_opt('function_arguments'))

    print(f"*** Function Result: {result}")
    if 'response' in result:
      inst.send_event('send_response', result['response'])
    if 'data' in result:
      for block in result['data']:
        inst.state['request_ctx'].append(block)
    if 'result' in result:
      inst.state['run_results'].append(result['result'])
    if 'entries' in result:
      pass
    # do something with success

  get_multiline_args.add_loop_entry(pc.entry.ChainFunctionEntry(set_multiline_state))
  ml_arg_value = get_multiline_args.add_loop_entry(pc.entry.ChainPromptEntry(name="get_arg"))
  ml_arg_value.add_message(app.prompts.get('functions/get-multiline-arg-sys'))
  ml_arg_value.parser('full_response', 'multiline_arg_value')
  ml_arg_set = get_multiline_args.add_loop_entry(pc.entry.ChainFunctionEntry(set_multiline_arg))
  ml_set_arguments = get_multiline_args.add_entry(pc.entry.ChainFunctionEntry(set_fn_args))
  fn_exec = choose_fn.add_entry(pc.entry.ChainFunctionEntry(call_function))

  # multiline_get_arg = get_multiline_args.add_loop_entry(PromptEntry())
  # Note: Maybe need custom class for this, or add state vars for each argument
  # multiline_get_arg.add_message("fill in this var:{{multiline_args_entry}}")
  # Custom entry to save to the arg name
  # Check function exists
  # Get function and:
  # - Prompt for each argument (single line vs multiline)
  # - Call function

  return chain

