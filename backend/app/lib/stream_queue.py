import threading
import time

class QueueThread:
  def __init__(self, default=""):
    self.queue = StreamQueue(default=default)

  def start(self, writer_fn, *args, **kwargs):
    self.thread = threading.Thread(target=writer_fn, args=args, kwargs=kwargs)
    self.thread.start()
  
  def finish(self):
    self.queue.finish()
    self.thread.join()

class StreamQueue:
  def __init__(self, default="", debug=False, opts={}):
    self.finished = False
    self.data = []
    self.opts = opts
    self.debug = debug
    self.default = default
    self._index = 0
    self.first_byte = None
    self.response = None
    self.data_wait = threading.Event()

  def __iter__(self):
    return self

  def __next__(self):
    if not self.finished or self._index < len(self.data):
      if self._index < len(self.data):
        self._index += 1
        return self.data[self._index - 1]
      else:
        # TODO: This isn't quite right.
        self.data_wait.clear()
        self.data_wait.wait(20)
        return self.default
    else:
      raise StopIteration

  def finish(self):
    self.finished = True
    self.data_wait.set()
    if self.debug:
      sys.stdout.write("\n")

  def write(self, data):
    self.append(data)

  def append(self, data):
    if self.finished:
      print("*** TQ: Got append after finish")
      return
    if not self.first_byte:
      self.first_byte = time.time()
    if self.debug:
      sys.stdout.write(data)
      sys.stdout.flush()
    self.data.append(data)
    self.data_wait.set()