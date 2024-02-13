# A full query runner for vector/db system.

# Usage:
# query = RAGQuery(app)
# results = query.query(1, "What is ...?")
# results[0].store_id
# results[0].chunk
# results[0]....
class RAGQuery:
  def __init__(self, app, **kwargs):
    self.app = app

  # query: A string to query the vector database
  # vector_result_count: Number of results to return from the vector database
  # max_results: Maximum results to return
  # filters: Filtering. Options: {'parent_id', 'store_id'}
  # cb: A callback function for status updates
  def query(self, query, vector_result_count=10, max_results=5, **kwargs):
    cb = kwargs['cb'] if 'cb' in kwargs else None
    self.call_cb(cb, {'message': 'Querying vector store'})
    query_embedding = self.app.embed.embedding(query).tolist()
    initial_results = self.query_vector_db(query_embedding, vector_result_count)
    self.call_cb(cb, {'message': 'Reranking results'})
    self.rerank(query, initial_results, **kwargs)
    #def sort_rank(entry):
    #  return entry.rank
    initial_results.sort(key=lambda entry: entry.rank, reverse=True)
    results = initial_results[0:max_results]
    return results

  def call_cb(self, cb, data):
    if cb is not None:
      cb(data)

  def rerank(self, query, results, **kwargs):
    if kwargs.get('skip_rerank', False):
      for r in results:
        r.rank = r.distance
      return
    result_content = [ r.content for r in results ]
    for idx,rank in enumerate(self.app.embed.ranking(query, result_content)):
      results[idx].rank = rank

  def query_vector_db(self, embedding, results=10, filters={}):
    # TODO: Add filters
    q_results = self.app.vector.collection.query(
      query_embeddings=[embedding],
      n_results=results,
    )

    results = []
    for idx,q_entry in enumerate(q_results['metadatas'][0]):
      entry = Result(
        vector_id=q_results['ids'][0][idx],
        distance=q_results['distances'][0][idx],
        content=q_results['documents'][0][idx],
        metadata=q_entry,
      )
      results.append(entry)
    return results

class Result:
  def __init__(self, **kwargs):
    metadata = self.get_from_dict(kwargs, 'metadata', {})
    self.entry = None
    self.vector_id = self.get_from_dict(kwargs, 'vector_id')
    self.distance = self.get_from_dict(kwargs, 'distance')
    self.rank = self.get_from_dict(kwargs, 'rank', self.distance)
    self.chunk_idx = self.get_from_dict(metadata, 'chunk_idx')
    self.entry_id = metadata.get('entry_id', None)
    self.content = kwargs.get('content', '')
    self.chunk = self.get_from_dict(metadata, 'chunk', '')
    self.store_id = self.get_from_dict(metadata, 'store_id')
    self.user_id = self.get_from_dict(metadata, 'user_id')
    self.vector_md = metadata

  def get_from_dict(self, data, name, default=None):
    if name in data:
      return data[name]
    return default

  def to_dict(self, **kwargs):
    result = {}
    for key in ['entry', 'vector_id', 'distance', 'rank', 'chunk_idx', 'chunk',
        'entry_id', 'content']:
      result[key] = self.__getattribute__(key)

    if 'entry' in kwargs and kwargs['entry']:
      result['entry'] = self.entry.to_dict()
    return result
