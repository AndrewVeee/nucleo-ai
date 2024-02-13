from .ai_model_base import AIBaseModel, ChainRunner
from ai_tools import prompt_chain as pc
from app.lib.string_tools import fill_prompt
from app.ai_models import function_chain
import time

Settings = {
  'app': None,
  'fns': None,
  'chain': None,
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
    instance.state[self.results] = []
    app = instance.get_opt('cfg')['app']
    fn_context = []
    instance.state['request_ctx'] = fn_context
    fn_chain = function_chain.create_function_chain(app)
    model = instance.get_opt('model')
    for idx,task in enumerate(tasks):
      instance.send_event('status', {'value': f"Running task {idx+1} of {len(tasks)} - {task}"})
      runner = ChainRunner(fn_chain, model, handler=model.chain_event,
        state={
          'message': instance.state['message'],
          'task': task,
          'task_list': instance.state[self.task_list],
          'request_ctx': fn_context,
          'run_results': instance.state[self.results]
        },
      )
      # Run FunctionChain here
      runner.instance.set_opt('cfg', instance.get_opt('cfg'))
      runner.instance.set_opt('run_fn', True)
      runner.run()
      #result = self.run_task(task, instance)
      #if 'error' in result:
      #  instance.send_event('status', {'value': f"Error Running Task: {task} ({result['error']})"})

    return {'response': None, 'children': self.children}

def init_chain(app):
  fns = app.ai_functions
  Settings['app'] = app
  Settings['fns'] = fns
  Settings['chain'] = chain = pc.PromptChain()

  # Prompt to get initial list of tasks.
  task_overview = Settings['chain'].add_prompt_entry("Task Overview")
  task_overview.add_message(app.prompts.get('assistant/overview-sys'), 'system')
  task_overview.add_message(app.prompts.get('assistant/overview-user'))
  task_overview.parser("list", "task_overview")
  task_overview.add_event('status', 'task_overview')
  task_overview.add_event('status', 'Making task list...', send_type="text")
  
  # Initialize task_list to empty list
  list_init = pc.entry.ChainStateSetter('task_list', setter=lambda: [], chain=Settings['chain'])
  task_overview.add_entry(list_init)

  # For each item in task_overview, we will use the task-breakdown prompt
  # to ask for the items to be broken into individual steps.
  task_breakdown = pc.entry.ChainForEachEntry("task_overview")
  list_init.add_entry(task_breakdown)

  bd_entry = task_breakdown.add_loop_entry(pc.entry.ChainPromptEntry(name="Breakdown"))
  bd_entry.add_message(fill_prompt(app.prompts.get('assistant/breakdown-sys'), {
    'assistants': fns.entry_list_string(),
    'tools': fns.all_functions_string(),
    'examples': fns.example_string(),
  }, enc=["{", "}"]), "system")
  bd_entry.add_message("- {{task_overview_entry}}")
  bd_entry.parser('list', 'partial_task_list', event="status")

  # Use MergeTasks entry to add each item in partial_task_list to the full task_list
  task_list = bd_merge = bd_entry.add_entry(MergeTasks('partial_task_list', 'task_list', chain=Settings['chain']))
  
  fn_loop = task_breakdown.add_entry(TaskLoop("task_list", chain=Settings['chain']))
  fn_loop.add_event('status', "Completed!", send_type="text")
  response = fn_loop.add_prompt_entry("send_response")
  response.set_opt('response', True)
  response.add_message(app.prompts.get('assistant/response-sys'))

  # Create a ForEach chain that each task_list entry
  # Run a new function chain for each task
  # Need shared state for each task. Maybe the ForEach is part of the chain?
  # Initialize with message, context list (needs append feature), and task list/current task


class AssistantModel(AIBaseModel):

  def chain_event(self, event, data, entry):
    if event != 'response':
      print(f"received: {event} - {data}")
    if event == 'response':
      #self.tq.queue.append(self.generate_block(data))
      if entry.get_opt('response'):
        self.tq.queue.append(self.generate_block(data))
      else:
        print(f"{data}", end="")
        #self.tq.queue.append(self.generate_block('', {'part': data}))
    elif event == 'send_response':
      self.tq.queue.append(data)
    elif event == 'status':
      self.tq.queue.append(self.generate_block('', {'event': 'status', 'data': data}))

  def get_chain(self):
    if Settings['chain'] == None:
      init_chain(self.app)
    return Settings['chain']

  def chat_stream(self, messages):
    print(f" * Run Prompt: {messages}")
    return self.llm.chat_stream(messages, stream_args={'temperature': 0})

  def handler(self, messages, tq, cfg={}):
    chain = ChainRunner(self.get_chain(), self, handler=self.chain_event,
      state={
        'message': messages[-1]['content']
      },
    )
    chain.instance.set_opt('model', self)
    chain.instance.set_opt('cfg', cfg)
    chain.run()
    self.tq.queue.append(self.generate_block('', {'event': 'status', 'status': chain.instance.state['task_list']}))
    self.tq.queue.finish()

  def run(self, messages, cfg={}, **kwargs):
    self.tq = self.create_thread_queue(default=self.generate_block(""))
    self.tq.start(self.handler, cfg=cfg, tq=self.tq, messages=messages)
    for chunk in self.tq.queue:
      yield chunk
