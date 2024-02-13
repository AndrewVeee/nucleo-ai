# Context Manager

Drop in a no-dependency context manager in to your code for chat history, rag, and more.

## What It Does

- This allows for an "infinite" chat system, where you can store the log in a database and have access to a long history of chat messages that are relevant to the request.
- Add dynamic content that is included when it ranks. You can add this before the loop:
  ```
  # Add date/time
  ctx.add_dynamic('dt', 'current date and time',
    fn=lambda: datetime.now().strftime("Current Date: %Y-%m-%d, Current Time: %I:%M%P"))
  # Add some sample text
  ctx.add_dynamic('content-ex', 'ContextManager chat history example', content="This is an example of using ContextManager 
  for a simple chat with history.")
  ```
  When the user asks "What's the date?", that function will rank and be included in the results.
- Want to add RAG to your results? You can add this above the ctx.generate_messages() line:
  ```
  rag_results = search_rag(req, max=30)
  for rag_res in rag_results:
    if rag_res['score'] > 0.2:
      ctx.add_ephemeral(f"Context: {rag_res['filename']}\n```\nrag_res\n```", cm.Roles.system)
  ```
  Now, when the user asks "What's an overview of Top Secret Project?", your RAG injects as much context as you want, and the context manager fills it with the results after leaving room for the last_messages=10, and current request.

## Usage

Copy the context_manager directory to your project, then:

```python
import context_manager as cm
# Set up a context manager with 1024 tokens.
# It will try to include the last 10 messages automatically.
# For older messages, it will use SimpleRanker to determine what else to include in the history.
ctx = cm.ContextManager(max_tokens=1024, last_messages=10, ranker=cm.SimpleRanker().rank)

# Add your AI generation code here
def stream_response(messages):
  result = f"I'm not a real AI, but you said: {messages[-1]['content']}"
  print(result)
  return result

system_message = "You're an intelligent, sarcastic spy named Lana Kane, helping your new partner."
while True:
  req = read("> ")
  # Start a new request
  ctx.start_new_message()
  # Add the system message, include_text=False means that it won't use the system text for ranking.
  ctx.request(system_message, role=cm.Roles.system, include_text=False)
  # Add the current message from the user
  ctx.request(req)
  # Generate the list of messages to send to the AI
  messages = ctx.generate_messages()
  
  # Send the messages to the AI of your choice and get the response.
  response = stream_response(messages)
  
  # Add the user message and response to the history
  ctx.add_message(req)
  ctx.add_message(response, cm.Roles.assistant)
  # Now, as it loops, the messages added will be included based on context size, last N messages, + ranking for older messages
```

## Overview

```
import context_manager as cm
ctx = cm.ContextManager(max_tokens=1024, last_messages=10, ranker=cm.SimpleRanker().rank)
```
Initializes a context manager with:
- max_tokens=1024: Max of 1024 tokens
- last_messages=10: (Optional) Prioritizes adding the last 10 chat messages to the context
- ranker=cm.SimpleRanker.rank: (Optional) Uses a built-in simple ranker that ranks content by word occurences. Using a cross_encoder from SentenceTransformers will improve ranking substantially
- token_counter=my_token_counter: (Optional) Provide a token counter function that takes a message string and returns the size. The default counter assumes 4.3 characters per token.

```
ctx.add_dynamic('dt', 'current date and time',
    fn=lambda: datetime.now().strftime("Current Date: %Y-%m-%d, Current Time: %I:%M%P"))
```
Adds a dynamic field:
- name 'dt': Gives it a name so if it's added a second time, it will overwrite the current setting.
- text 'current data and time': Text content used to generate ranking.
- fn=lambda...: (Optional) Provides a function to call to generate the message content.
- content="...": Instead of fn, you can use this to provide text for the message content.

```
ctx.start_new_message()
```
Clears the current ephemeral and request lists to start a new message.

```
ctx.request(system_message, role=cm.Roles.system, include_text=False)
ctx.request(user_request)
```
Adds a new message to the current request:
- message: The text content of the message
- role=cm.Roles.{system,assistant,user}: (Optional - user is default) Sets the role for the message
- include_text: (Optional, True is default) Whether to include the message content when ranking.
  For system messages like "You are a helpful assistant...", the text would probably make ranking less accurate.

```
ctx.ephemeral("Chunk of text")
```
Adds temporary content (RAG data, for example) to the current request that will be included if it ranks based on the Ranker. When start_new_message() is called, this will be cleared. See add_dynamic above if you want to add it permanently to the context.

```
ctx.generate_messages()
# Result: [{'role': 'role-name', 'content': 'message content'}, ...]
```
Generates the list of messages to send to an LLM. Combines all dynamic, ephemeral, and previous message data to the current request. It works by filling the messages up to max_tokens with the following priority:
- The current request() messages.
- {last_messages} previous messages.
- Ranking the dynamic, ephemeral, and past messages, then including them based on their score.

```
ctx.add_message(content, role=cm.Roles.user)
```
Adds a new message to the message history:
- content: The content of the message
- role: Optional, default is user) Role of the message
Once the message is added, it will be included when using generate_messages(). That means for user message + LLM response, you should add these after calling generate_message() so it isn't included twice.

## Future Ideas/Wishlist

This is a small library written in a couple of days, and will likely change over time.

- Ranking: Provide an example with a cross_encoder ranking system.
- Import/Export: Allow exporting the message history so it can be saved and imported.
- Client/Server Example: Create a small demo of using this with a client that saves the state.
- Advanced Ordering: Add advanced ordering for message history, RAG results, etc.
