import re

def set_md_headers(cur_headers, level, text):
  headers = []
  for i in range(level-1):
    if len(cur_headers) > i:
      headers.append(cur_headers[i])
    else:
      headers.append('')
  headers.append(text)
  return headers

HEADER_RE = re.compile("^(#+) +(.*)$")

def gen_meta(title, headers, max_meta, sep=" - ", max_head=40, min_head=10):
  meta = ''
  remaining = max_meta
  if len(headers):
    meta += headers[-1][0:max_meta]
    remaining = max_meta - len(meta)
  
  if title and remaining > len(sep):
    if len(meta) > 0:
      meta += sep
      remaining -= len(sep)
    meta += title[0:remaining if remaining < max_head else max_head]
    remaining = max_meta - len(meta)
  for idx,text in enumerate(headers):
    if idx == len(headers) - 1:
      break
    if remaining > len(sep):
      remaining -= len(sep)
      meta += sep + text[0:remaining if remaining < max_head else max_head]
    remaining = max_meta - len(meta)
  return meta  
  
# Create markdown chunks using headers as separators and use
# headers + title to include metadata in the chunk.
def markdown_splitter(text, max_len=1024, **kwargs):
  title = kwargs.get('title', None)
  max_meta = kwargs.get('max_meta_len', 30)
  add_meta = kwargs.get('add_meta', True)
  include_headers = kwargs.get('include_headers', False)
  meta_pref = kwargs.get('meta_prefix', 'Topic: ')
  headers = []
  cur_head = ''
  cur_level = 0
  cur_text = ''
  chunks = []

  for line in text.split("\n"):
    match = HEADER_RE.fullmatch(line)
    if match:
      # Chunk current text/meta before updating.
      if cur_text.strip() != '':
        for chunk in split_text(
          cur_text.strip(),
          max_len,
          meta_pref + gen_meta(title, headers, max_meta) + "\n" if add_meta else ''
        ):
          chunks.append(chunk)
      h_lvl = len(match[1])
      cur_head = match[2]
      cur_level = h_lvl
      headers = set_md_headers(headers, cur_level, cur_head)
      cur_text = cur_head + "\n" if include_headers else ''
    else:
      cur_text += line + "\n"
  if cur_text.strip() != '':
    for chunk in split_text(cur_text.strip(), max_len, meta_pref + gen_meta(title, headers, max_meta) + "\n"):
      chunks.append(chunk)

  return chunks

# TODO: Fix extra newlines and lines longer than max_len
def split_text(text, max_len=1024, metadata=''):
  chunks = []
  cur_chunk = metadata
  cur_chunk_len = len(cur_chunk)

  for line in text.split("\n"):
    line_len = len(line)
    if cur_chunk_len + line_len > max_len:
      if cur_chunk != metadata:
        chunks.append(cur_chunk)
      if len(metadata + line) > max_len:
        for i in range(0, len(line), max_len - len(metadata)):
          chunks.append(metadata + line[i:i+max_len-len(metadata)])
        cur_chunk = metadata
        cur_chunk_len = len(cur_chunk)
      else:
        cur_chunk = metadata + line + "\n"
        cur_chunk_len = len(cur_chunk) #line_len
    else:
      cur_chunk += line + "\n"
      cur_chunk_len += line_len + 1

  if cur_chunk != '':
    chunks.append(cur_chunk)
  return chunks
