import threading

class QueueWorker:
  def __init__(self, queue):
    self.queue = queue

  def start(self):
    self.thread = threading.Thread(target=self.run,)
    self.thread.daemon = True
    self.thread.start()

  def run(self):
    while True:
      if self.queue.stopped:
        return
      item = self.queue.get_next_job()
      if item is not None:
        item.run()

class JobItem:
  def __init__(self, handler, opts, priority):
    self.handler = handler
    self.opts = opts
    self.priority = priority
    self.finished = threading.Event()
    self.result = None
    self.exception = None
  
  def wait(self):
    self.finished.wait()
    return self.result

  def run(self):
    try:
      self.result = self.handler(self.opts)
    except Exception as e:
      print(f"Job Exception: {e}")
      self.exception = e
    self.finished.set()

class JobQueue:
  def __init__(self, runners=1, start_now=True, name='untitled'):
    self.name = name
    self.run_count = runners
    self.queue = []
    self.stopped = False
    self.jobs_available = threading.Event()
    self.workers = []
    if start_now:
      self.start()
  
  def start(self):
    for i in range(self.run_count):
      worker = QueueWorker(self)
      worker.start()
      self.workers.append(worker)

  def stop(self):
    self.stopped = True

  def add(self, handler, opts, priority=5):
    job = JobItem(handler, opts, priority)
    self.queue.append(job)
    self.queue.sort(key=lambda job: job.priority, reverse=True)
    self.jobs_available.set()
    return job

  def get_next_job(self):
    self.jobs_available.wait(60)
    try:
      return self.queue.pop(0)
    except Exception as e:
      self.jobs_available.clear()
      return None
