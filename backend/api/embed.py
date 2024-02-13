import os

class Embed:
  def __init__(self, app):
    self.app = app;
    server = app.server
    server.add('/api/embed/stats', self.stats)
    server.add('/api/v1/embed', self.embed)
    server.add('/api/v1/rank', self.rank,
        methods=['POST'], auth=True)
    server.add('/api/v1/upload', self.upload, auth=True)
    server.add('/api/embed/get', self.db_get)
    server.add('/api/embed/del', self.db_del)
    server.add('/api/embed/search', self.search, auth=True,
      doc="Search the RAG system", args=["query", 'count'])

  def db_del(self, req, res, user):
    args = {}
    json = req.json
    for opt in ['ids', 'where']:
      if opt in json:
        args[opt] = json[opt]
    return self.app.vector.collection.delete(**args)

  def db_get(self, req, res, user):
    args = {}
    json = req.json
    for opt in ['ids', 'where', 'n_results', 'where_document', 'include']:
      if opt in json:
        args[opt] = json[opt]
    return self.app.vector.collection.get(**args)

  def stats(self, req, res, user):
    return {
      'peek': self.app.vector.collection.peek(),
      'count': self.app.vector.collection.count(),
    }
  def search(self, req, res, user):
    results = self.app.embed.search.query(req.json['query'],
      vector_result_count=req.json.get('vector_results', 30),
      max_results=req.json.get('max_results', 20)
    )
    return [result.to_dict() for result in results]

  def embed(self, req, res, user):
    return {
      'result': [float(val) for val in self.app.embed.embedding(req.json['content'])],
    }

  def rank(self, req, res, user):
    query = req.json['query']
    results = req.json['results']
    
    return {'ranks': self.app.embed.ranking(query, results)}

  def upsert(self, req, res, user):
    entry = {
      "user_id": user.id,
      "shared": req.json.get("shared", False),
      "type": req.json.get("type", "note"),
      "parent_id": req.json.get("parent_id", None),
      "collection": req.json.get("collection", None),
      "name": req.json.get("name", "untitled"),
      "source": req.json.get("source", None),
      "stored_name": req.json.get("stored_name", None),
      "meta": req.json.get("meta", None),
      "content": req.json.get("content", ""),
    }
    current = self.app.db.UserStore.where(
        type=entry['type'],
        parent_id=entry['parent_type'],
        collection=req['collection'],
        name=req['name']
    )
    return entry

  def upload(self, req, res, user):
    if 'file' not in req.files:
      raise Exception("No file provided")
    file = req.files['file']
    # TODO: Get collection, shared, parent_id
    upload = self.app.db.UserStore.create(user_id=user.id, shared=False, 
        name=file.filename, type='file')
    new_filename = f"{upload.id}-{file.filename}"
    req.files['file'].save(os.path.join('../data/uploads/', new_filename))
    upload.stored_name = new_filename
    upload.save()
    upload.process()
    return upload.to_dict()
