import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

class FireStore:
  db = None
  db_name = ""

  def __init__(self, collection_name, db_name = "(default)"):
    pass

  def get_record_by_key(self, key):
    record = self.db.document(key).get()
    return record.to_dict()
  
  def get_all_records(self, limit = 10):
    results = []
    docs = self.db.limit(limit).stream()
    for doc in docs:
      results.append(doc.to_dict())
    return results
  
  def update_record_by_key(self, key, data):
    self.db.document(key).update(data)

  def create_record_by_key(self, key, data, is_merge = True):
    self.db.document(key).set(data, is_merge)

  def create_record(self, data):
    update_time, ref = self.db.add(data)
    return ref.id
  


# testing
# x = FireStore("users").get_record_by_key("WqHL5ov8s8UMefVbtTdPAu8cEfP2")
# print(str(x))
# x = FireStore("chats").create_record_by_key("5Akq7ae9aLm1RRf7txEe", {"test22": "aa", "awefa": "eafaw"})
# print(str(x))