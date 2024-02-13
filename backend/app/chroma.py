import chromadb

class VectorDB:
  def __init__(self, app, dir='../data/', config={}, **kwargs):
    self.app = app
    self.embed_name = config.get('db_name', 'test')
    self.dist_fn = config.get('dist_fn', 'cosine')
    # generate full dir based on embed_model config
    self.chroma = chromadb.PersistentClient(path=f"{dir}/chroma-{self.embed_name}/")
    self.default_count = 10
    self.init_collection()

  def init_collection(self, name='vectors'):
    try:
      self.collection = self.chroma.get_collection(name=name)
    except:
      self.collection = self.chroma.create_collection(name=name,
          metadata={'hnsw:space': self.dist_fn}
      )

  def delete(self, **kwargs):
    args = {}
    if 'where' in kwargs:
      args['where'] = kwargs['where']
    if 'ids' in kwargs:
      args['ids'] = kwargs['ids']
    return self.collection.delete(**args)

  # replace with upsert
  # chunk handling
  def add(self, **kwargs):
    # add embedding, text, meta
    #docs = [kwargs['doc'] if 'doc' in kwargs else '']
    #embed = [kwargs['embedding'] if 'embedding' in kwargs else None]
    #meta = [kwargs['metadata'] if 'metadata' in kwargs else {}]
    #ids = [kwargs['id'] if 'id' in kwargs else None]
    args = {}
    for key in ['documents', 'embeddings', 'metadata', 'ids']:
      if key in kwargs:
        args[key] = kwargs[key]

    self.collection.add(**args)

  # cv.query(embedding, where={"user_id":1,collection:'contacts',...})
  def query(self, embed, **kwargs):
    return self.collection.query(
      query_embeddings=[embed],
      n_results=kwargs['count'] if 'count' in kwargs else self.default_count,
      where=kwargs['where'] if 'where' in kwargs else {}
    )
