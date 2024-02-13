from .ai_model_base import AIBaseModel, ChainRunner
from ai_tools.prompt_chain import PromptChain
import time

MessageChain = PromptChain()

def init_chain():
  summary = MessageChain.add_prompt_entry("Summarize")
  summary.add_message("We just received this message:\n```\n{{message}}\n```\n\nWrite a one sentence summary as the sender to explain briefly what the message is about.")
  summary.parser("full_response", "summary", event="summary")
  summary.set_opt('response', True)

  category = summary.add_prompt_entry("Categorize")
  category.add_message((
    "You're a helpful bot that categorized income messages. Summary:\n```\n{{summary}}\n```\n\n"
    "Categorize the message as:\npersonal: A personal message.\nnotification: Only newsletters and social media notifications\nbill: Notifications for payments, bills and invoices from companies.\nad: An advertisement or spam.\n\n"
    "Respond with one line: Category: <category name>"))
  category.parser("from_line", "category", parser_opts="Category:", event="category")
  category.set_opt('temperature', 0)

  bill_info = category.add_prompt_entry("Bill Extract")
  bill_info.condition("category", "includes", "bill")
  bill_info.add_message("We received this message:\n```\n{{message}}\n```\nExtract relevant billing info like total cost, due date, payment link, and description.")
  bill_info.parser("full_response", "bill", event="bill")
  #bill_info.set_opt('response', True)

  replies = category.add_prompt_entry("Suggest replies")
  replies.condition("category", "includes", "personal")
  replies.set_opt('temperature', 0.5)
  replies.add_message("We received a message. Here's the summary:\n```\n{{summary}}\n```\nSuggest 4 reply option summaries, including yes/no options.")
  replies.parser("full_response", "replies", event="suggest_replies")
  #replies.set_opt('response', True)

init_chain()

class MessageModel(AIBaseModel):

  def chain_event(self, event, data, entry, inst):
    if event == 'response':
      #self.tq.queue.append(self.generate_block(data))
      if entry.get_opt('response'):
        self.tq.queue.append(self.generate_block(data))
      else:
        self.tq.queue.append(self.generate_block('', {'part': data}))
    elif data and 'value' in data['data']:
      self.tq.queue.append(self.generate_block('', {'event': event, 'data': data['data']['value']}))

  def handler(self, messages, tq):
    chain = ChainRunner(MessageChain, self.llm, handler=self.chain_event,
      state={
        'message': messages[-1]
      },
      app=self.app,
    )
    chain.run()
    self.tq.queue.finish()

  def run(self, messages, **kwargs):
    self.tq = self.create_thread_queue(default=self.generate_block(""))
    self.tq.start(self.handler, tq=self.tq, messages=messages)
    for chunk in self.tq.queue:
      yield chunk
