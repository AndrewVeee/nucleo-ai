## Nucleo AI Alpha

An AI assistant app that mixes AI features with traditional personal productivity. The
AI can work in the background to answer multiple chats, handle tasks, and stream/feed entries.

Here's a demo video:

https://github.com/AndrewVeee/nucleo-ai/assets/153542699/60526628-62f5-462f-a6a4-affdbdb6d7c1

For the curious: This demo was recorded using OpenHermes Mistral 7b through llama.cpp.

**Warnings**:
This is "alpha" software. It is new. There are bugs and issues.

Some features (esp the assistant mode) can use a lot of tokens. Be aware when you
are trying this with paid APIs. This is an early release and there are bugs and
improvements needed.

### Install and Setup

You should have Python 3 and git installed. I've tried to keep the app light-weight,
but RAG requires downloading some large files (about 850mb for the embed and cross encoder).

The app does not include the LLM engine. You can connect it to any openai-compatible endpoint, like llama.cpp, oobabooga with
the --api flag, and newer versions of ollama. I use llama-cpp-python and
together ai quite a bit.

#### Step 1
```
$ git clone git@github.com:AndrewVeee/nucleo-ai.git

# Create python venv, install torch cpu-only and requirements.txt. Copy config file.
$ ./setup.sh
```

#### Step 2

Edit the config file in `./data/config.toml`

Find the `[llm]` block and set your `openai_base_url` (something like http://localhost:5000/v1) and
the `openai_api_key` if required. You can also set the `secret_key` at the top if you want to require auth to
connect to Nucleo.

#### Step 3

Run `./start.sh` to start the app. The first run will take a bit to download the
SentenceTransformers models for RAG support.


### Features

#### Regular Chat

Nucleo supports regular chat. You can create multiple chats, and choose saved or
temporary (throwaway) chat when you create it.

#### Assistant

The Assistant chat mode has the AI make a list of tasks from the request and perform them.
It can perform web searches, add to do entries, create docs, and respond.

This is very early, and most models will make mistakes. Mixtral tends to do pretty well.
I personally use OpenHermes Mistral 7b for testing, and it has ~50% success rate unless
you are very careful with the wording.

#### Docs (RAG)

You can upload PDFs (I recommend < 5mb right now) in the Docs tab or upload plain text/markdown files. You can create new
docs at the top, or paste in a URL to download and convert it to markdown.

With files uploaded, you can enable the Docs chat mode and it should do a decent job of
finding relevant content and responding. Of course, this is dependent on your model. For small
context models, make sure to set the "Past Messages" chat option low or there won't be much room for
RAG results.

#### Stream

The stream tab shows a list of actions the assistant has performed. You can also add one-shot
chats to your stream - Assistant Task, Quick Chat, or Message (paste emails, etc to categorize
and summarize). When you create entries, you can replay them later.

#### To Do

There is a very basic to do list in the app, so the AI can create entries for you. You
can add, editor, or remove entries through the tab.

### What's Next?

Right now, I'm primarily looking for feedback and ideas, to know how far it is from a daily driver
for others.

I have some ideas I really want to try:

- Researcher: In the stream, enter a topic and let the AI run for a few minutes, choosing
  subtopics, running web searches, and writing its findings in a "live document".
- Assistant Modes: There are many ways to implement the assistant mode, from quick 1- or 2-shot
  requests, to complex ReAct LLM loops. I want to experiment with multiple options, some for
  tiny models, some for large models.
- Stream/Feed: I want to have useful integrations with things like email, calendar, and other personal
  data sources, so it can all be in one place, and the AI can reference it.
- More Functions: Each function makes the assistant more useful, and I'd like to have a list of
  popular requests to build.
- Fine Tuned Models: It would be really nice to have a tiny fine-tuned model (like TinyLlama, Phi, etc)
  that can handle an assistant mode.

### Developers

My long term goal for Nucleo is a platform that helps developers build and test ideas and make them available
to others to try easily. I'm not a fan of most LLM frameworks, so I'd prefer Nucleo as a collection of tools
that you can pick and choose as you need.

The code is pretty messy, but here are some key points to play around:

- You can take a look at `app/functions/functions.py` if you want to add your own function.
- Nucleo is API-first. You can connect to it at `/api/v1/chat/completions` with an OpenAI
  client.
- Nucleo uses "virtual" models. You can set the model to 'assistant' to chat in assistant mode,
  'chat' to chat in basic mode, or 'message' to summarize messages.
- With chat mode, you can also append a message with {'role': 'config', 'content': '{"rag": true}'}
  to enable RAG in the chat.
- One of the key future features is being able to create your own virtual models, but
  it's currently a pretty messy process. Take a look at `backend/app/ai_models/default_model.py` to
  see the chat model, or assistant_model2.py for a complex example.

There's so much work to do. I'm happy to help if you want to contribute.

### Getting Help

Need help?

- You can post issues here.
- I've set up a subreddit to discuss and ask for help as well:
  https://www.reddit.com/r/nucleoai/
