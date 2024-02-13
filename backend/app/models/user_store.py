from app.sqlite_table import Table
from app.lib import text_helpers

#from app.lib import pdf, text_helpers

# Table: user_data
# Columns:
# - user_id: user id
# - data_type: data type (eg "todo", "doc", "file", "note", "folder", "dir", etc)
#   Note: folders are UI folders, dirs are for future directory uploads/syncing
# - subtype: If the datatype needs subtype info (eg "stream" - "log")
# - root_id: For nested structures, id of the root
# - parent_type: Type of parent (string)
# - parent_id: ID of the parent, if any.
# - name: Name/title of the entry
# - metadata: JSON string containing additional info
# - content: Full content of the entry
# - ai_created: True if entry was created by AI
class UserStore(Table):
  table_name = 'user_store'
  table_columns = ['user_id', 'data_type', 'subtype', 'root_id', 'parent_type', 'parent_id', 'name', 'metadata',
      'content', 'pinned', 'source', 'embed_model', 'ai_created', 'created_at', 'updated_at']

  def remove_embeds(self):
    cls = self.__class__
    res = cls.app.vector.collection.delete(where={'entry_id': str(self.id)})

  def update_embed(self):
    cls = self.__class__
    self.remove_embeds()
    self.embed_model = cls.app.vector.embed_name
    chunks = text_helpers.markdown_splitter(
      self.content,
      max_meta_len=50, max_len=512, title=self.name,
    )
    docs = []
    embeddings = []
    metadata = []
    ids = []
    for idx,chunk in enumerate(chunks):
      embeddings.append(cls.app.embed.embedding(chunk).tolist()),
      ids.append(f"ent-{self.id}-{idx}")
      docs.append(chunk)
      metadata.append({
        'data_type': self.data_type,
        'entry_id': str(self.id),
        'chunk_idx': idx,
      })

    return cls.app.vector.collection.upsert(documents=docs, embeddings=embeddings, metadatas=metadata, ids=ids)
