# TODO:
# - Finish save() and add update()
# - Figure out column data typs

from datetime import datetime

# Base class for sqlite tables
class Table:
  @classmethod
  def init(cls, db, app):
    cls.app = app
    cls.db = db
    cls.migrate()

  @classmethod
  def migrate(cls):
    if cls.table_name not in cls.db.table_names:
      print(f"Create table {cls.table_name}")
      cols = ",".join([f"{col} string" for col in cls.table_columns])
      cls.db.exec(f'create table {cls.table_name} (id integer primary key autoincrement, {cols})')
    cursor = cls.db.conn.cursor()
    cursor.execute(f'select * from {cls.table_name} limit 0')
    table_cols = [desc[0] for desc in cursor.description]
    for col in cls.table_columns:
      if col not in table_cols:
        print(f"Add column to {cls.table_name}: {col}")
        cls.db.exec(f'alter table {cls.table_name} add column {col} string')

  @classmethod
  def create(cls, **kwargs):
    cols = []
    values = []
    ctime = str(datetime.now())
    full_ent = {}
    for col in cls.table_columns:
      if col == 'id' and 'id' not in kwargs:
        continue
      val = kwargs.get(col, None)
      if (col == 'created_at' or col == 'updated_at') and val is None:
        val = ctime
      full_ent[col] = val
      cols.append(col)
      values.append(val)

    sql = f"insert into {cls.table_name} ({','.join(cols)}) values ({','.join(['?' for col in cols])})"
    res = cls.db.exec(sql, values)
    id = res[1].lastrowid
    full_ent['id'] = id
    ent = cls(full_ent, is_new=False)
    return ent

  @classmethod
  def count(cls):
    sql = f"select count(*) from {cls.table_name}"
    res = cls.db.exec(sql)
    return res[0].fetchall()[0][0]

  @classmethod
  def find(cls, id):
    sql = f"select * from {cls.table_name} where id=? limit 1"
    res = cls.db.exec(sql, [id])
    columns = {}
    row = res[0].fetchall()[0]
    for idx,col in enumerate(res[1].description):
      columns[col[0]] = row[idx]
    return cls(columns, is_new=False)

  @classmethod
  def all(cls):
    return cls.where()

  @classmethod
  def delete_where(cls, **kwargs):
    query = 'delete '
    where = None
    query_args = []
    query += f" from {cls.table_name}"
    if 'where' in kwargs:
      where = cls.gen_where(**kwargs['where'])
      query += f" where {where['clause']}"
      query_args = where['args']

    cls.app.log(f"DELETE: {query} [{query_args}]", level=3)
    res = cls.db.exec(query, query_args)
    results = []
    for row in res[0]:
      data = {}
      for idx,col in enumerate(res[1].description):
        data[col[0]] = row[idx]
      results.append(cls(data, is_new=False))
    return results  

  @classmethod
  def select(cls, **kwargs):
    query = 'select '
    where = None
    query_args = []
    if 'fields' in kwargs:
      query += kwargs['fields']
    elif 'exclude' in kwargs:
      query += 'id, ' + ', '.join([
        col for col
        in cls.table_columns
        if col not in kwargs['exclude']
      ])
    else:
      query += '*'
    query += f" from {cls.table_name}"
    if 'where' in kwargs:
      where = cls.gen_where(**kwargs['where'])
      query += f" where {where['clause']}"
      query_args = where['args']
    if 'order' in kwargs:
      column = kwargs['order'][0]
      sort = kwargs['order'][1]
      if sort.lower() not in ['desc', 'asc']:
        sort = 'asc'
      if column in cls.table_columns:
        query += f" order by {column} {sort}"
    
    cls.app.log(f"SELECT: {query} [{query_args}]", level=3)
    res = cls.db.exec(query, query_args)
    results = []
    for row in res[0]:
      data = {}
      for idx,col in enumerate(res[1].description):
        data[col[0]] = row[idx]
      results.append(cls(data, is_new=False))
    return results  

  @classmethod
  def gen_where(cls, *args, **kwargs):
    if len(args) > 0:
      #print(f"query={args[0]} ({args[1]})")
      return {
        'clause': args[0],
        'args': args[1]
      }
    else:
      q_cols = []
      q_vals = []
      for col in kwargs.keys():
        if kwargs[col] is None:
          q_cols.append(f"{col} is null")
        else:
          q_cols.append(f"{col}=?")
          q_vals.append(kwargs[col])
      where_clause = ' and '.join([col for col in q_cols])
      if len(kwargs.keys()) == 0:
        where_clause = '1=1'
      return {
        'clause': where_clause,
        'args': q_vals
      }

  @classmethod
  def where(cls, *args, **kwargs):
    query = None
    query_args = []
    if len(args) > 0:
      #print(f"query={args[0]} ({args[1]})")
      query = f"select * from {cls.table_name} where {args[0]}"
      query_args = args[1]
    else:
      q_cols = []
      q_vals = []
      for col in kwargs.keys():
        if kwargs[col] is None:
          q_cols.append(f"{col} is null")
        else:
          q_cols.append(f"{col}=?")
          q_vals.append(kwargs[col])
      where_clause = ' and '.join([col for col in q_cols])
      if len(kwargs.keys()) == 0:
        where_clause = '1=1'
      query = f"select * from {cls.table_name} where {where_clause}"
      query_args = q_vals
      #print(f"query keys={q_cols} ({q_vals})")
    res = cls.db.exec(query, query_args)
    results = []
    for row in res[0]:
      data = {}
      for idx,col in enumerate(res[1].description):
        data[col[0]] = row[idx]
      results.append(cls(data, is_new=False))
    return results
        
  def to_dict(self):
    res = {'id': self.__getattribute__('id')}
    for key in self.__class__.table_columns:
      res[key] = self.__getattribute__(key)
    return res

  def __init__(self, columns={}, is_new=True):
    cls = self.__class__
    self._is_new = is_new
    self._orig_values = {}
    self.id = columns['id'] if 'id' in columns else None
    for col in cls.table_columns:
      if col in columns:
        self.__setattr__(col, columns[col])
        self._orig_values[col] = columns[col]
      else:
        self._orig_values[col] = None
        self.__setattr__(col, None)

  def delete(self):
    id = self.id
    sql = f"delete from {self.__class__.table_name} where id=?"
    res = self.__class__.db.exec(sql, [id])
    return res

  def save(self):
    cols = []
    values = []
    for col in self.__class__.table_columns:
      cols.append(col)
      values.append(self.__getattribute__(col))
    if 'updated_at' in self.__class__.table_columns:
      cols.append('updated_at')
      values.append(datetime.now())
    if self._is_new:
      sql = f"insert into {self.__class__.table_name} ({','.join(cols)}) values ({','.join(['?' for col in cols])})"
      res = self.__class__.db.exec(sql, values)
      self.id = res[1].lastrowid
      self._is_new = False
    else:
      values.append(self.id)
      sql = f"update {self.__class__.table_name} set {', '.join([f'{col}=?' for col in cols])} where id = ?"
      res = self.__class__.db.exec(sql, values)
