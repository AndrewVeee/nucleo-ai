from .ai_model_base import AIBaseModel
from app.lib import stream_queue, string_tools, text_helpers, web

from ai_tools import context_manager as cm
from ai_tools.prompt_chain import chain

from datetime import datetime
import time

def load_prompt(app, prompt_name, data):
  prompt = app.prompts.get(prompt_name)
  return string_tools.fill_prompt(prompt, data)

# Data class to hold topics that have been researched as a
# nested list.
class ResearchTopic:
  def __init__(self, title, id=None, depth=0):
    self.title = title
    self.id = id
    self.content = ''
    self.refs = []
    self.depth = depth
    self.children = []

  def generate_md(self):
    if self.content == '':
      md = '#' * (self.depth + 1) + ' [*Not Researched*] ' + self.title + "\n\n"
    else:
      md = '#' * (self.depth + 1) + ' ' + self.title + "\n\n"
      if self.content != '':
        md += self.content
      else:
        md += "*Not enough time to research this topic*"
    
    for child in self.children:
      md += "\n\n" + child.generate_md()
    
    if len(self.refs) > 0:
      md += "\n\n## References\n\n"
      for idx,ref in enumerate(self.refs):
        md += f"[{idx+1}] [{ref['title']}]({ref['url']})\n"

    return md

  def print(self):
    print("#" * (self.depth + 1), self.title)
    print(self.content,"\n", self.refs)
    for child in self.children:
      child.print()

# Class to run the main research loop.
class Researcher:
  def __init__(self, topic, topics, model, tq, **kwargs):
    self.topic = topic
    self.generate_block = model.generate_block
    self.model = model
    self.app = model.app
    self.tq = tq
    self.topics = topics
    self.last_id = 0
    self.search_id = 0
    self.downloads = {}
    self.priority = kwargs.get('priority', 5)
    self.max_time = kwargs.get('max_time', 2)
    self.max_time = float(self.max_time) * 60
    self.max_depth = int(kwargs.get('max_depth', 2))
    self.subtopic_count = str(kwargs.get('subtopic_count', 3))
    self.web_search = kwargs.get('websearch', False)
    self.min_rank = kwargs.get('min_rank', -5)
    self.paragraphs = str(kwargs.get('paragraphs', 1))
    self.temperature = kwargs.get('temperature', 0)
    self.writing_instructions = kwargs.get('writing_instructions', "")
    self.result = self.add_topic(None, topic)
    self.explore_list = []
    self.content_ctx = cm.ContextManager(
      max_tokens=self.app.llm.context_size * 0.8,
      ranker=self.app.embed.ranking,
      min_rank=self.min_rank,
    )
    for topic in topics:
      sub_topic = self.add_topic(self.result, topic)
      self.explore_list.append(sub_topic)
  
  def add_topic(self, parent, title):
    self.last_id += 1
    depth = parent.depth + 1 if parent else 0
    topic = ResearchTopic(title, self.last_id, depth=depth)
    if parent:
      parent.children.append(topic)
    else:
      return topic
    return topic

  def generate_doc(self):
    pass

  def time_left(self):
    return self.max_time - (time.time() - self.start)

  def run_prompt(self, messages, opts={}):
    job = self.app.llm_queue.add(self.model.run_llm, {
      'messages': messages,
      'stream_args': opts.get('stream_args', {'temperature': self.temperature}),
      'cb': opts.get('cb', None)
    }, self.priority)
    job.wait()
    return job.result

  def search_and_download(self, query):
    search = web.DDGSearch()
    search.run_search(query)
    url = search.results[0]['href']
    if url in self.downloads:
      return {'existing': True, 'url': url, 'title': self.downloads[url], 'chunks': []}
    self.app.debug(f"Downloading URL: {url}")
    retriever = web.URLRetriever()
    retriever.get_url(url, timeout=10)
    self.app.debug(f"Converting to markdown")
    md = retriever.get_markdown()
    self.downloads[url] = retriever.title
    # Rough calc: 2k tok context * 4 = 8k chars. 2k / 5 = 400 chars (100 tokens)
    # Top 5 chunks = 500 tokens (25% of context size)
    #chunks = text_helpers.split_text(md, int(self.app.llm.context_size / 5))
    chunks = text_helpers.markdown_splitter(md, int(self.app.llm.context_size / 5),
      add_meta=False, include_headers=True)
    return {
      'existing': False,
      'url': url,
      'title': retriever.title,
      'chunks': chunks,
    }

  def send_update(self, text, data):
    self.tq.queue.append(self.generate_block(text, data))

  def send_status(self, value):
    self.send_update(None, {'event': 'status', 'data': {'value': value}})
    
  def research_topic(self, topic, ctx, search=True, subtopics=True):
    # Generate parent topic string
    downloaded_url = None
    if search and self.web_search:
      self.send_status(f"Generating search topic for {topic.title}")
      # TODO: Use the generated topic string to set the topic_overview var
      prompt = load_prompt(self.app, 'researcher/search_query', {
        'main_topic': self.result.title,
        'current_topic': topic.title,
      })
      result = self.run_prompt([
        {'role': 'system', 'content': prompt}
      ])
      query = chain.parse_from_line(result, 'search:').strip('"')
      if query == '':
        self.app.debug("[Researcher] No search: found.", [result, topic.title])
        query = topic.title
      self.app.debug("[Researcher] Search", query)
      self.send_status(f"Searching for {query}")
      try:
        results = self.search_and_download(query)
        downloaded_url = results['url']
        self.search_id += 1
        if not results['existing']:
          self.result.refs.append({
            'title': results['title'],
            'url': results['url']
          })
      except Exception as e:
        self.app.log("Web Search Exception", e)
        results = {'url': '', 'title': '', 'chunks': []}
      self.app.debug("[Researcher] Search Result", self.search_id, results['url'], results['title'],
          len(results['chunks']))
      for idx,chunk in enumerate(results['chunks']):
        self.content_ctx.add_dynamic(f"search_{self.search_id}_{idx}", f"Web Snippet (Reference: {self.search_id}):\n'''\n{chunk}\n'''", content=None, role='user')

    ex_str = f" with {downloaded_url}" if downloaded_url else ''
    self.send_status(f"Generating prompt for {topic.title}{ex_str}")
    prompt_top = load_prompt(self.app, 'researcher/write_response_top', {
      'main_topic': self.result.title,
      'topic': topic.title,
      'paragraphs': str(self.paragraphs),
    })
    prompt_bottom = load_prompt(self.app, 'researcher/write_response_bottom', {
      'main_topic': self.result.title,
      'topic': topic.title,
      'paragraphs': str(self.paragraphs),
    })
    self.content_ctx.start_new_message()
    self.content_ctx.request(prompt_top, 'system', top=True)
    self.content_ctx.request(prompt_bottom, 'user')
    messages = self.content_ctx.generate_messages(from_text=topic.title)

    self.send_status(f"Writing content for {topic.title}{ex_str}")
    self.app.debug("[Researcher] Generating", [self.content_ctx.last_rank_text, len(messages)])
    result = self.run_prompt(messages, opts={
      'cb': lambda chunk: self.send_update(None, {'event': 'live_content', 'data': {'id': topic.id, 'text': chunk}})
    })
    topic.content = result

    if self.time_left() > 0 and self.max_depth > topic.depth and subtopics == True:
      self.send_status(f"Generating subtopics for {topic.title}")
      prompt = load_prompt(self.app, 'researcher/list_subtopics', {
        'main_topic': self.result.title,
        'topic': topic.title,
        'count': self.subtopic_count,
      })
      result = self.run_prompt([
        {'role': 'system', 'content': prompt}
      ])
      for entry in chain.parse_list(result, None):
         sub_top = self.add_topic(topic, entry)
         self.explore_list.append(sub_top)
      #print("Subtopics", result.split("\n"))

  def run(self):
    self.start = time.time()
    # ctx_search = ContextManager(...)
    ctx_search = None
    while True:
      self.send_update(None, {'event': 'time', 'data': {'total': self.max_time, 'left': self.time_left()}})
      if self.time_left() <= 0 or len(self.explore_list) == 0:
        break
      topic = self.explore_list.pop(0)
      self.research_topic(topic, ctx=ctx_search)

    # Generate the final, top section
    ctx_primary = cm.ContextManager(
      max_tokens=self.app.llm.context_size * 0.8,
      ranker=self.app.embed.ranking,
      min_rank=self.min_rank,
    )
    # add all content to the context manager
    prelim_doc = self.result.generate_md()
    chunks = text_helpers.markdown_splitter(prelim_doc, int(self.app.llm.context_size / 7),
      add_meta=False, include_headers=True)
    for idx,chunk in enumerate(chunks):
      ctx_primary.add_dynamic(f"chunk_{idx}", f"Doc Snippet:\n'''\n{chunk}\n'''", content=None, role='user')
    ctx_primary.start_new_message()
    prompt_top = load_prompt(self.app, 'researcher/final_response_top', {
      'main_topic': self.result.title,
      'paragraphs': str(self.paragraphs),
    })
    prompt_bottom = load_prompt(self.app, 'researcher/final_response_bottom', {
      'main_topic': self.result.title,
      'paragraphs': str(self.paragraphs),
    })
    ctx_primary.request(prompt_top, 'system', top=True)
    ctx_primary.request(prompt_bottom, 'user')
    messages = ctx_primary.generate_messages(from_text=self.result.title)

    self.send_status(f"Writing final content for {self.result.title}")
    self.app.debug("[Researcher] Generating", [ctx_primary.last_rank_text, len(messages)])
    result = self.run_prompt(messages, opts={
      'cb': lambda chunk: self.send_update(None, {'event': 'live_content', 'data': {'id': self.result.id, 'text': chunk}})
    })
    self.result.content = result
    #self.research_topic(self.result, ctx=ctx_primary, search=False, subtopics=False)
    content = self.result.generate_md()
    self.send_update(None, {'event': 'document', 'data': {'content': content}})
    return self.result

class ResearcherModel(AIBaseModel):
  def run_llm(self, opts):
    self.app.debug("[Researcher:run_llm]", opts['messages'])
    tq = opts.get('tq', None)
    cb = opts.get('cb', None)
    response = ''
    for chunk in self.llm.chat_stream(opts['messages'], stream_args=opts['stream_args']):
      response += chunk
      if tq:
        tq.queue.append(self.generate_block(chunk))
      if cb:
        cb(chunk)
    return response

  def handler(self, tq, **kwargs):
    chat_opts = self.default_opts(kwargs)
    req_config = kwargs['request_config']
    
    # If topics are provided, run the main research loop, otherwise generate the topic list.
    if 'topics' in req_config:
      self.app.log("Research topics:", req_config['topics'])
      researcher = Researcher(req_config.get('topic'), req_config.get('topics'),
        model=self, tq=tq,
        priority=req_config.get('priority', 5),
        websearch=req_config.get('websearch', True),
        subtopic_count=req_config.get('subtopic_count', 3),
        max_depth=req_config.get('max_depth', 2),
        max_time=req_config.get('max_time', 2),
        temperature=req_config.get('temperature', 0),
        paragraphs=req_config.get('paragraphs', 2),
        writing_instructions=req_config.get('writing_instructions', ''),
      )
      researcher.run()
    else:
      prompt = self.app.prompts.get('researcher/list_topics')

      job = self.app.llm_queue.add(self.run_llm, {
        'messages': [
          {'role': 'system', 'content': string_tools.fill_prompt(prompt, {'topic': req_config.get('topic')})}
        ],
        'stream_args': chat_opts,
        #'tq': tq,
      }, priority=req_config.get('priority', 5))
      job.wait()
      tq.queue.append(self.generate_block("\n".join(chain.parse_list(job.result, None))))
    tq.queue.finish()

  def run(self, messages, tq=None, **kwargs):
    if tq is None:
      tq = self.create_thread_queue(default="")
    tq.start(self.handler, tq=tq, messages=messages, **kwargs)
    for chunk in tq.queue:
      yield chunk
    tq.finish()