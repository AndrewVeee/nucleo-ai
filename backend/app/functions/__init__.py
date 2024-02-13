from ai_tools.functions import function_list
from app.functions import functions

# Singleton function list instance
Functions = function_list.FunctionList()

# Add top-level entries. Functions should be added to one of these.
Functions.add_entry("Secretary", "Managing to do lists, calendar, people.", examples=[
  "Add a to do entry to run errands."
])
Functions.add_entry("Writer", "Draft emails, documents.", examples=[
  "Draft email about top secret project."
])
Functions.add_entry("Artist", "Creating and editing media", examples=[
  "Take a photo of a beautiful sunset."
]).fn_descriptions = ['take photos', 'draw', 'edit media']
Functions.add_entry("Researcher", "Reading documents, files, web searches.", examples=[
  "Look up bird watching."
]).fn_descriptions = ['find, research']

#fns.add_entry("Artist", "Work with multimedia content.")

# This entry should be last. It is meant to detect tasks that can't be handled.
Functions.add_entry("General", "Other tasks not handled above.", auto_fail=True). \
  fn_descriptions = ['tasks not handled']

def init(app):
  functions.WebSearch(app)
  functions.AddToDo(app)
  functions.SendResponse(app)
  functions.CreateDoc(app)