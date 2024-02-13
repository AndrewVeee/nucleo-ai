# Promp Chains

Prompt chains allow you to run multiple prompts and conditionally run other based on the output and state.

Goals:

- Make it easy to create and run multiple prompts.
- Simple, customizable chains without a framework controlling everything.
- Easily debuggable, and useful events for displaying information to users.
- Little to no dependencies, with pluggable LLM execution.

## Quick Tutorial

For this tutorial, we'll create a simple chain allows an AI assistant to categorize and summarize a new message.

```python
# Import the library
import prompt_chain

# Create a message handler chain
message_chain = prompt_chain.PromptChain('Message Handler')

# Add the first prompt to the chain
summarizer = message_chain.add_prompt_entry('summarize')
# Add a prompt tellling the AI what to do
summarizer.add_message("Summarize the following message:\n```\n{{message}}\n```\nWrite the summary as the original sender in one sentence.", "system")
# Save the full output to the state as "summary" using the parser named full_response.
# The chain state is a simple key-value dict.
# Event is optional, but we'll use it here to trigger an event named summarized.
summarizer.parser("full_response", "summary", event="summarized")

# Add a prompt that runs after the summarizer to categorize the message.
# Notice we use the {{summary}} variable instead of message - the summary should be smaller so should speed things up.
categorize = summarizer.add_prompt_entry('categorize')
categorize.add_message("Categorize the following message:\n```\n{{summary}}\n```\nCategorize the message as a bill, personal, ad, or automated. Just reply with Category: <type>")
# Use the from_line parser to look for Category: <x>
categorize.parser("from_line", "category", parser_opts="category:")

```




