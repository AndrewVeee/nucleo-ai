import sqlite3
from app.sqlite_table import Table
#from app.models.user import User
#from app.models.vector_data import VectorData
#from app.models.user_store import UserStore
from app.models.user_store import UserStore

class Database:
  def __init__(self, app, db="../data/app.sqlite3"):
    self.app = app
    self.conn = sqlite3.connect(db, check_same_thread=False)
    column_res = self.exec('select name from sqlite_master where type="table"')[0].fetchall()
    self.table_names = [fields[0] for fields in column_res]
    self.register([UserStore])
    self.UserStore = UserStore

  def register(self, classes):
    for cls in classes:
      cls.init(self, self.app)

  def exec(self, query, args=()):
    cursor = self.conn.cursor()
    result = cursor.execute(query, args)
    self.conn.commit()
    return [result, cursor]
