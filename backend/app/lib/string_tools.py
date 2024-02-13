
def fill_prompt(content, state, enc=['{{', '}}']):
  for key in state.keys():
    content = content.replace(f"{enc[0]}{key}{enc[1]}", state[key])
  return content