from app.lib import pdf

import os
import time
#import argon2
#import jwt

def get_opt(opts, key, default=None):
  return opts[key] if key in opts else default

def set_opt(to_dict, from_dict, key, req=None, new_key=None):
  val = get_opt(from_dict, key, req)
  if val is None:
    return
  to_dict[new_key if new_key else key] = val

class Store:
  def __init__(self, app):
    self.app = app;
    server = app.server
    server.add('/api/store/list', self.list)
    server.add('/api/store/vector_search', self.vector_search)
    server.add('/api/store/delete', self.delete)
    server.add('/api/store/delete_match', self.delete_match)
    server.add('/api/store/update', self.update)
    server.add('/api/store/create', self.create)
    server.add('/api/store/upload', self.upload)

  def vector_search(self, req, res, user):
    query = req.json['query']
    results = self.app.embed.search.query(query,
      vector_result_count=req.json.get('vector_results', 30),
      max_results=req.json.get('max_results', 30),
    )
    return [
      #{
      #  'distance': res.distance, 'rank': res.rank,
      #  'id': res.entry_id, 'content': res.content,
      #}
      res.to_dict() for res in results
    ]
    self.app.log("RAG Query:", msg, level=2)
    self.app.log("RAG Results:", [[round(res.rank,2), res.content[0:75]] for res in results], level=3)
    for res in results:
      ctx.add_ephemeral(f"Context (Ref:{res.entry_id})\n```\n{res.content}\n```",
          role=cm.Roles.user)

  def upload(self, req, res, user):
    if 'file' not in req.files:
      raise Exception("No file provided")
    file = req.files['file']
    entry = {
      'data_type': 'doc',
      'metadata': '{}',
      'name': file.filename,
    }
    upload = self.app.db.UserStore.create(**entry)
    new_filename = f"{upload.id}-{file.filename}"
    self.app.debug(f"store/upload Saving {new_filename}")
    full_path = os.path.join("../data/uploads/", new_filename)
    req.files['file'].save(full_path)
    if new_filename.endswith('.pdf'):
      self.app.debug(f"store/upload Converting pdf to markdown")
      upload.content = pdf.pdf_to_markdown(full_path)
    else:
      with open(full_path) as f:
        upload.content = f.read()
    self.app.debug(f"store/upload Update embeddings")
    upload.update_embed()
    upload.source = f"/uploads/{new_filename}"
    upload.save()
    self.app.debug(f"store/upload Done")
    return upload.to_dict()

  def create(self, request, res, user):
    entry = {'metadata': '{}'}
    self.app.debug(f"store/create Init fields")
    for field in self.app.db.UserStore.table_columns:
      set_opt(entry, request.json, field)
    self.app.debug(f"store/create Create entry")
    entry = self.app.db.UserStore.create(**entry)
    if entry.content is not None and entry.content != '':
      self.app.debug(f"store/create Update embeddings")
      entry.update_embed()
      self.app.debug(f"store/create Save")
      entry.save()
    self.app.debug(f"store/create Done")
    return entry.to_dict()

  def update(self, request, res, user):
    entry = self.app.db.UserStore.find(request.json['id'])
    content_changed = False
    for field in self.app.db.UserStore.table_columns:
      if field in request.json and field != 'id' and field != 'embed_model':
        if field == 'content':
          content_changed = True
        setattr(entry, field, request.json[field])
    if content_changed:
      entry.update_embed()
    entry.save()
    return entry.to_dict()

  def delete_match(self, request, res, user):
    where_args = {}
    req = request.json

    set_opt(where_args, req, 'data_type')
    set_opt(where_args, req, 'root_id')
    set_opt(where_args, req, 'parent_type')
    set_opt(where_args, req, 'parent_id')
    set_opt(where_args, req, 'id')
    return [
      entry.to_dict() for entry in
      self.app.db.UserStore.delete_where(
        where=where_args,
      )
    ]


  def delete(self, request, res, user):
    id = request.json['id']
    entry = self.app.db.UserStore.find(id)
    entry.remove_embeds()
    entry.delete()
    return {'deleted': True}

  def list(self, request, res, user):
    where_args = {}
    ex_args = {}
    req = request.json

    set_opt(where_args, req, 'data_type')
    set_opt(where_args, req, 'root_id')
    set_opt(where_args, req, 'parent_type')
    set_opt(where_args, req, 'parent_id')
    set_opt(where_args, req, 'id')
    if '_exclude' in req:
      ex_args['exclude'] = req['_exclude']
    order = req.get('order', ['created_at', 'desc'])
    return [
      entry.to_dict() for entry in
      self.app.db.UserStore.select(
        where=where_args,
        order=order,
        **ex_args,
      )
    ]

