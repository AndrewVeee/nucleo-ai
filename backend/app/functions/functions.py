from app.lib import web, text_helpers
import json

class WebSearch:
  def __init__(self, app):
    self.app = app
    self.reg = app.ai_functions.define(self.run, 'web_search', 'Search the web',
        short_description="look ups, web searches")
    self.reg.add_argument('query', 'A good google search query to get this information',
      question="What search query should we use?"
    )
    self.reg.add_to('Researcher')
 
  def run(self, instance, args):
    return self.run_first_res(instance, args)

  # Current Method:
  # Run the requested query, download the first page,
  # and return the top 4 chunks related to the query.
  def run_first_res(self, instance, args):
    query = args.get('query', None)
    if query is None:
      return {
        'success': False,
        'response': 'Error performing web search. No query provided.\n\n',
      }
    search = web.DDGSearch()
    search.run_search(args['query'])
    url = search.results[0]['href']
    retriever = web.URLRetriever()
    retriever.get_url(url)
    md = retriever.get_markdown()
    # Rough calc: 2k tok context * 4 = 8k chars. 2k / 5 = 400 chars (100 tokens)
    # Top 5 chunks = 500 tokens (25% of context size)
    chunks = text_helpers.split_text(md, int(self.app.llm.context_size / 5))
    top_5 = self.app.embed.ranker.top_n(args['query'], chunks, n=4)
    return {
      'success': True,
      'result': f"Retrieved results for {args['query']}",
      #'data': search.result_list(),
      'data': top_5,
    }

  # Old:
  # Just retrieve the result list and return the url/title/snippet.
  def run_simple_res(self, instance, args):
    #original_request = args['request']
    query = args.get('query', None)
    if query is None:
      return {
        'success': False,
        'response': 'Error performing web search. No query provided.\n\n',
      }
    search = web.DDGSearch()
    search.run_search(args['query'])
    return {
      'success': True,
      'result': f"Retrieved results for {args['query']}",
      'data': search.result_list(),
    }
    search_string = search.result_string()
    prompt = (
      f"We are answering the following request:\n```{original_request}\n```\n\n"
      f"We have the following results:\n```\n{search_string}\n```\n\n"
      "Does this result already have the information we need to answer the request?\n"
      "Respond with one line:\nAnswered: yes or no"
    )
    result = self.app.llm.chat_result(messages= [
      {'role': 'system', 'content': prompt}
    ])
    if 'yes' in result:
      return result_str
    
    prompt = (
      f"We are answering the following request:\n```{original_request}\n```\n\n"
      f"We have the following results:\n```\n{result_str}\n```\n\n"
      "Which URL above is most likely to have the information we need?\n"
      "Respond with one line:\nURL: <url>"
    )
    result = self.app.llm.chat_result(messages= [
      {'role': 'system', 'content': prompt}
    ])
    url = result.match(r".*(https?.*)", '$1')[0]
    return {
      'success': True,
      'message': 'Looked up ' + original_request,
      'data': self.chunks(self.convert_url_to_md(url))
    }

class AddToDo:
  def __init__(self, app):
    self.app = app
    self.reg = app.ai_functions.define(self.run, 'add_todo', 'Add item to to do list',
        short_description="to do lists")
    self.reg.add_argument('entry_content', 'Short text for the to do list entry.', question="What to do entry should we add?")
    self.reg.add_to('Secretary')
  
  def run(self, instance, args):
    field = 'entry_content'
    if field not in args:
      return {
        'success': False,
        'result': f"Error adding to do entry for {instance.state['task']}",
        'response': f"Sorry, I didn't write a title for the new to-do entry."
      }
    todo_entry = args[field]
    new_entry = self.app.db.UserStore.create(
      data_type="todo",
      ai_created=True,
      name=todo_entry,
      content=''
    )
    stream = self.app.db.UserStore.create(
      data_type="stream", subtype="log",
      ai_created=True,
      name=new_entry.name,
      metadata=json.dumps({'type':'todo', 'id':new_entry.id})
    )
    return {
      'success': True,
      'result': f"Added to do entry: {todo_entry}",
      'entries': [
        new_entry.to_dict(), stream.to_dict(),
      ],
      'response': f"I've created a new to do entry for you: {todo_entry}\n"
    }

class CreateDoc:
  def __init__(self, app):
    self.app = app
    self.reg = app.ai_functions.define(self.run, 'create_doc', 'Create a new document',
        short_description="write docs")
    self.reg.add_argument('title', 'A short title for the document.', question="What is the title of the document?")
    self.reg.add_argument('content', 'Write the document content in markdown format.', multiline=True, question="What is the contents of the document?")
    self.reg.add_to('Writer')
  
  def run(self, instance, args):
    title = args['title']
    content = args['content']
    new_entry = self.app.db.UserStore.create(
      data_type="doc",
      ai_created=True,
      name=title,
      content=content
    )
    stream = self.app.db.UserStore.create(
      data_type="stream", subtype="log",
      ai_created=True,
      name=new_entry.name,
      metadata=json.dumps({'type':'doc', 'id':new_entry.id})
    )
    return {
      'success': True,
      'result': f"Created doc: {args['title']}",
      'entries': [
        new_entry.to_dict(), stream.to_dict(),
      ],
      'response': f"I've created a new doc for you titled {args['title']}\n"
    }

class SendResponse:
  def __init__(self, app):
    self.app = app
    self.reg = app.ai_functions.define(self.run, 'respond_user', 'Respond to the user, answer, or suggest.',
        short_description="responses")
    self.reg.add_argument('response', 'Write only the response. Be very concise, but cite URLs in markdown, if available.',
      multiline=True, question="What should we respond with?",
      stream_response=True,
    )
    self.reg.add_to('Writer')
  
  def run(self, instance, args):
    return {
      'success': True,
      'message': f"Responded",
      'response': None,
      #'response': args['response'] + "\n"
    }