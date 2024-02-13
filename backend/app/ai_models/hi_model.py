from .ai_model_base import AIBaseModel, ChainRunner
from ai_tools.prompt_chain import PromptChain
import time

TestChain = PromptChain()
def init_chain():
  res = TestChain.add_prompt_entry("Response")
  res.add_message("{{message}}")
  res.set_opt('response', True)
init_chain()

class HiModel(AIBaseModel):

  def chain_event(self, event, data, entry):
    if event == 'response':
      if entry.get_opt('response'):
        self.tq.queue.append(self.generate_block(data))
      else:
        self.tq.queue.append(self.generate_block('', {'part': data}))

  def handler(self, messages, tq):
    chain = ChainRunner(TestChain, self.llm, handler=self.chain_event)
    chain.run()
    self.tq.queue.finish()

  def run(self, messages, **kwargs):
    self.tq = self.create_thread_queue(default=self.generate_block(""))
    self.tq.start(self.handler, tq=self.tq, messages=messages)
    for chunk in self.tq.queue:
      yield chunk
