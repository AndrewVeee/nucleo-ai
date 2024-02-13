from .ai_model_base import AIBaseModel
from app.lib import stream_queue
from ai_tools import context_manager as cm
from datetime import datetime


class DefaultModel(AIBaseModel):

  def run_llm(self, opts):
    tq = opts['tq']
    for chunk in self.llm.chat_stream(opts['messages'], stream_args=opts['stream_args']):
      tq.append(self.generate_block(chunk))
    tq.finish()

  def make_ctx(self, messages, opts):
    ctx = cm.ContextManager(
      max_tokens=self.app.llm.context_size * 0.8,
      ranker=self.app.embed.ranking,
      last_messages=20,
    )
    for idx,msg in enumerate(messages):
      # TODO: Roles should be mapped to cm.Roles.system/user/assistant
      inc_text = idx == len(messages) - 1 # Only include most recent msg in rerank context
      ctx.request(msg['content'], msg['role'], include_text=inc_text)

    if opts.get('rag', False):
      ctx.add_dynamic('dt', 'Current date and time',
          fn=lambda: datetime.now().strftime("Current Date: %Y-%m-%d, Current Time: %I:%M%P"))
      msg = messages[-1]['content']
      results = self.app.embed.search.query(msg,
        vector_result_count=opts.get('vector_results', 30),
        max_results=opts.get('max_results', 30),
        skip_rerank=True
      )
      self.app.log("RAG Query:", msg, level=2)
      self.app.log("RAG Results:", [[round(res.rank,2), res.content[0:75]] for res in results], level=3)
      for res in results:
        ctx.add_ephemeral(f"Context (Ref:{res.entry_id})\n```\n{res.content}\n```",
            role=cm.Roles.user)
    return ctx

  def run(self, messages, **kwargs):
    tq = stream_queue.StreamQueue()

    chat_opts = self.default_opts(kwargs)
    req_config = kwargs['request_config']
    yield self.generate_block('', {'event': 'status', 'data': {'value': 'Generating context.'}})
    ctx = self.make_ctx(messages, req_config)
    messages = ctx.generate_messages()
    self.app.log("[Model:default]", messages, level=2)
    tq.append(self.generate_block('', {'event': 'status', 'data': {'value': None}}))
    job = self.app.llm_queue.add(self.run_llm, {
      'messages': messages,
      'stream_args': chat_opts,
      'tq': tq,
    }, priority=req_config.get('priority', 5))
    for chunk in tq:
      yield chunk
