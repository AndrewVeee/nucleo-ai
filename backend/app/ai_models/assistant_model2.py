from .ai_model_base import AIBaseModel, ChainRunner
from ai_tools import prompt_chain as pc
from app.lib.string_tools import fill_prompt
from app.ai_models import function_chain_simple

import re
import time

Settings = {
  'app': None,
  'fns': None,
}
AssistantChain = []

# Chain entry to append all tasks to a single list
class MergeTasks(pc.entry.ChainEntryBase):
  def __init__(self, state_partial, state_result, *args, **kwargs):
    self.state_partial = state_partial
    self.state_result = state_result
    super().__init__(self, *args, **kwargs)
  
  def runner(self, instance):
    partial_list = instance.state[self.state_partial]
    result_list = instance.state[self.state_result]
    for item in partial_list:
      result_list.append(item)
    return {'response': None, 'children': self.children}

class TaskLoop(pc.entry.ChainEntryBase):
  def __init__(self, task_list, *args, **kwargs):
    self.task_list = task_list
    self.store = f"{task_list}_data"
    self.results = f"{task_list}_results"
    super().__init__(self, *args, **kwargs)
  
  def run_task(self, task, instance):
    return {
      'success': True
    }

  def runner(self, instance):
    tasks = instance.state[self.task_list]
    instance.state[self.store] = ""
    instance.state['run_results'] = []
    app = instance.get_opt('cfg')['app']
    fn_context = []
    instance.state['request_ctx'] = fn_context
    fn_chain = function_chain_simple.create_function_chain(app)
    model = instance.get_opt('model')
    for idx,task in enumerate(tasks):
      instance.send_event('client:state', {'msg': f"Task {idx+1} of {len(tasks)}", 'level': 0})
      #instance.send_event('status', {'value': f"Running task {idx+1} of {len(tasks)} - {task}"})
      runner = ChainRunner(fn_chain, model, handler=model.chain_event,
        state={
          'message': instance.state['message'],
          'task': task,
          'task_list': instance.state[self.task_list],
          'request_ctx': fn_context,
          'run_results': instance.state['run_results']
        },
        app=app
      )
      # Run FunctionChain here
      runner.instance.set_opt('cfg', instance.get_opt('cfg'))
      runner.instance.set_opt('run_fn', True)
      runner.instance.set_opt('tq', instance.get_opt('tq'))
      runner.run()
      #result = self.run_task(task, instance)
      #if 'error' in result:
      #  instance.send_event('status', {'value': f"Error Running Task: {task} ({result['error']})"})

    return {'response': None, 'children': self.children}

task_re = re.compile(r".*Task: (.*)$")
def parse_tasks(inst, res, opts):
  tasks = []
  for line in inst.state['task_overview'].split("\n"):
    match = task_re.fullmatch(line)
    if match:
      tasks.append(match[1])
  inst.state['task_list'] = tasks

def create_chain(app):
  fns = app.ai_functions
  # TODO: Find out why chain roots are disappearing.
  #if 'chain' in Settings:
  #  return Settings['chain']
  chain = pc.PromptChain()
  Settings['chain'] = pc.PromptChain()

  # Prompt to get initial list of tasks.
  task_overview = chain.add_prompt_entry("Task Overview")
  task_overview.add_event('status', 'Making task list...', send_type="text", before_run=True)
  task_overview.add_message(app.prompts.get('assistant2/overview-sys'), 'system')
  task_overview.add_message("{{message}}")
  task_overview.parser("full_response", "task_overview")
  task_overview.add_event('status', 'task_overview')
  create_task_list = task_overview.add_entry(pc.entry.ChainFunctionEntry(parse_tasks))
  create_task_list.add_event('status', 'task_list')
  fn_loop = create_task_list.add_entry(TaskLoop("task_list", chain=chain))
  response = fn_loop.add_prompt_entry("send_response")
  response.set_opt('response', True)
  response.add_message(app.prompts.get('assistant2/response-sys'))

  return chain  

class AssistantModel(AIBaseModel):

  def chain_event(self, event, data, entry, inst):
    send_to_client = False

    if event.startswith("client:"):
      send_to_client = True
      event = event[7:]
    tq = inst.get_opt('tq')
  
    if event == 'response':
      stream_state = entry.stream_state
      should_stream = inst.state.get(stream_state, False) if stream_state else False
      if entry.get_opt('response') or should_stream:
        tq.queue.append(self.generate_block(data))
      else:
        print(f"{data}", end="")
    elif event == 'response_end':
      stream_state = entry.stream_state
      should_stream = inst.state.get(stream_state, False) if stream_state else False
      if should_stream:
        tq.queue.append(self.generate_block("\n\n"))
    elif event == 'send_response':
      tq.queue.append(self.generate_block(data['data']))
    elif event == 'status':
      tq.queue.append(self.generate_block('', {'event': 'status', 'data': data['data']}))
    elif send_to_client == True:
      tq.queue.append(self.generate_block('', {'event': event, 'data': data['data']}))

  def get_chain(self):
    chain = create_chain(self.app)
    return chain

  def chat_stream(self, messages, stream_args={}):
    print(f" * Run Prompt: {messages}")
    return self.llm.chat_stream(messages, stream_args)

  def handler(self, messages, tq, cfg={}):
    chain = ChainRunner(self.get_chain(), self, handler=self.chain_event,
      state={
        'message': messages[-1]['content']
      },
      app=self.app,
    )
    self.chain = chain
    chain.instance.set_opt('model', self)
    chain.instance.set_opt('cfg', cfg)
    chain.instance.set_opt('tq', tq)
    chain.instance.send_event('client:state', {'msg': "Making task list", 'level': 0})
    chain.run()
    #print(f"Finished chain {chain}")
    #self.tq.queue.append(self.generate_block('', {'event': 'status', 'status': chain.instance.state['task_list']}))
    tq.queue.finish()

  def run(self, messages, cfg={}, tq=None, **kwargs):
    if tq is None:
      tq = self.create_thread_queue(default="")
    #print(f"Assistant run: {tq}")
    tq.start(self.handler, cfg=cfg, tq=tq, messages=messages)
    for chunk in tq.queue:
      yield chunk
    tq.finish()
