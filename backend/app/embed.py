#!/usr/bin/env python3

from sentence_transformers import SentenceTransformer, CrossEncoder, util
from .lib.text_helpers import split_text
#from .lib.pdf import pdf_to_text
from .lib.rag_retriever import RAGQuery

class RAG:
  def __init__(self, app, config={}):
    self.app = app
    self.embed = Embedding(model=config.get('embed_model', 'BAAI/bge-small-en-v1.5'))
    self.ranker = Ranker(model=config.get('rank_model', 'cross-encoder/ms-marco-MiniLM-L-6-v2'))
    self.embedding = self.embed.embedding
    self.ranking = self.ranker.rerank
    self.search = RAGQuery(app)
    self.max_len = 512

  def generate_embeddings(self, text):
    chunks = split_text(text, self.max_len)
    return [
      self.embed.embedding(chunk) for chunk in chunks
    ]
    
class Ranker:
  def __init__(self, model='cross-encoder/ms-marco-MiniLM-L-6-v2'):
    self.cross_encoder = CrossEncoder(model)

  def rerank(self, query, data):
    comparisons = [[query, entry] for entry in data]
    return [float(val) for val in self.cross_encoder.predict(comparisons)]
  
  def top_n(self, query, data, n=5):
    data_ranks = list(zip(data, self.rerank(query, data)))
    data_ranks.sort(key=lambda entry: entry[1], reverse=True)
    return [
      data_rank[0]
      for data_rank in data_ranks[0:n]
    ]

class EmbedFromLlama:
  def __init__(self, llm):
    self.llm = llm

  def embedding(self, text):
    return self.llm.create_embedding(text)['data'][0]['embedding']

class Embedding:
  #def __init__(self, model='all-MiniLM-L6-v2'):
  def __init__(self, model='BAAI/bge-small-en-v1.5'):
    self.model = SentenceTransformer(model)

  def embedding(self, text):
    return self.model.encode([text])[0]
