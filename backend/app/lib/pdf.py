import fitz

class DocLine:
  def __init__(self, text, size, y):
    self.text = text
    self.size = size
    self.y = y

class PDF:
  def __init__(self, file):
    self.file = file
    self.doc = fitz.open(file)
    self.lines = []
    self.sizes = {}
    self.default_size = 12
    self.header_sizes = []

  def set_font_sizes(self):
    cur_size = 12
    cur_count = 0
    # Find regular font size
    for size in self.sizes:
      if self.sizes[size] > cur_count:
        cur_size = size
        cur_count = self.sizes[size]

    self.default_size = cur_size
    headers = []
    for size in self.sizes:
      if size > cur_size:
        headers.append([size, self.sizes[size]])
    headers.sort(key=lambda ent: ent[0], reverse=True)
    self.header_sizes = [size[0] for size in headers][0:4]

    return cur_size

  def get_header_from_sz(self, size):
    cur_diff = size - self.default_size
    header = None
    for idx,hd_sz in enumerate(self.header_sizes):
      diff = abs(hd_sz - size)
      if diff < cur_diff:
        cur_diff = diff
        header = idx
    return header

  def gen_md(self):
    md = ''
    last_head = 0

    for line in self.lines:
      head = None
      # Inserted line break
      if line.text == None:
        md += "\n"
        continue
      if line.size > self.default_size:
        head = self.get_header_from_sz(line.size)
      if head is not None and last_head == head:
        md += " " + line.text
      else:
        if md != '':
          md += "\n"
        if head != None:
          md += ("#" * (head + 1)) + " "
        md += line.text

      last_head = head
    return md

  def load(self):
    for page in self.doc:
      self.read_page(page)
    self.set_font_sizes()

  def read_page(self, p):
    #blocks = p.get_text("dict", sort=True, flags=11)['blocks']
    blocks = p.get_text("dict", sort=False)['blocks']

    last_y = None
    for b in blocks:
      if 'lines' not in b:
        #print("*** No lines found", b['ext'])
        continue
      for l in b['lines']:
        #print(l)
        cur_y = l['spans'][0]['origin'][1]
        line = DocLine("", 0, cur_y)
        for s in l['spans']:
          line.text += s['text']
          if line.size == 0:
            line.size = int(s['size'])
        if line.size not in self.sizes:
          self.sizes[line.size] = 0
        self.sizes[line.size] += 1

        # Check y change
        if last_y != None and cur_y - last_y > line.size * 2:
          #print(f"---Inject Blank (Diff:  {cur_y-last_y} >{line.size * 2})\n")
          self.lines.append(DocLine(None, line.size, cur_y))
        self.lines.append(line)
        last_y = cur_y

def pdf_to_markdown(filename):
  pdf = PDF(filename)
  pdf.load()
  return pdf.gen_md()

def pdf_to_text(filename):
  doc = fitz.open(filename, filetype='pdf')
  return "".join([p.get_text() for p in doc])
  #return "".join([p.get_text().encode('utf8') for p in doc])