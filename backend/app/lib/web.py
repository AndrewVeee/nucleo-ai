import re
import requests
from markdownify import MarkdownConverter
from bs4 import BeautifulSoup

try:
  from duckduckgo_search import DDGS
except:
  print("duckduckgo lib missing. Try pip install -U duckduckgo_search")

class WebPage:
  def __init__(self):
    pass

class DDGSearch:
  def __init__(self):
    self.results = []

  def run_search(self, query, results=4):
    try:
      with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=results)]
    except:
      # Create fake results
      results = []
    self.results = results
    return results
  
  def result_list(self):
    return [
      f"URL: {res['href']}\nTitle: {res['title']}\nContent: {res['body']}"
      for res in self.results
    ]
  def result_string(self):
    result_str = "\n".join(self.result_list())

class URLRetriever:
  def __init__(self):
    self.content = ''
    self.title = None
  
  def get_url(self, url):
    req_headers = {
      'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
      'Accept-Encoding': 'gzip, deflate',
      'Accept': '*/*',
      'Connection': 'keep-alive'
    }
    self.content = requests.get(url, headers=req_headers).content.decode('utf-8')
    return self.content
 
  def get_markdown(self):
    soup = BeautifulSoup(self.content, "html.parser")
    body = soup.find('body')
    title = soup.find('title')
    if title:
      self.title = title.text
    for tag in ['style', 'script']:
      for el in body.select(tag):
        el.extract()

    return MarkdownConverter(
      strip=['head', 'style', 'script'],
      heading_style='ATX',
    ).convert_soup(body)

  def get_text(self, tags=['title','h1','h2','h3','h4','h5','h6','p','table','ul','ol','li','section','div']):
    soup = BeautifulSoup(self.content, "html.parser")
    text = ""
    for tag in tags:
      text += "\n".join([element.get_text() for element in soup.find_all(tag)]) + "\n"
    self.text = text
    return text