import sys
import argparse
import re
import json
import os
from urllib import request as req
import random
import xmltodict
import urllib.parse
import requests

def make_url(keywords, serch_type="question"):
  '''
  wikipediaに投げるクエリ作成
  '''
  root_url = 'https://ja.wikipedia.org/w/api.php'
  
  query = ['format=xml',
           'utf8=',
           'action=query',
           'prop=revisions',
           'rvprop=content',
           'redirects',
           'titles='+urllib.parse.quote('|'.join(keywords)),
           ]
  
  url = '{}?{}'.format(root_url, '&'.join(query))
  return url

def db_access(query):
  '''
  レファレンス協同DBにクエリ投げる
  '''
  results = requests.get(query)
  results = xmltodict.parse(results.text)
  # print(results)
  ret = results['api']['query']['pages']['page']
  # print(ret)
  # print(type(ret))
  
  if not isinstance(ret, list):
    ret = [ret]
  # print(ret)
  # print(type(ret))
  
  ret = [x for x in ret if 'revisions' in x]
  # print(json.dumps(ret, indent=2, ensure_ascii=False))
  
  return ret

def parse_result(keywords, result):
  '''
  クエリレスポンスをパースしてほしいデータを抽出
  input:
    - keywords: キーワードのリスト
    - result: 検索結果
  output: 辞書データ
  '''
  
  # ページタイトル
  title = result['@title']
  # print(f'title: {title}')
  # print()
  
  # 本文
  text = result['revisions']['rev']['#text']
  # print(f'text:\n{text}')
  # print()
  
  # ヒットしたキーワード
  hits = [x for x in keywords if x in title]
  hit = None if len(hits)==0 else random.choice(hits)
  if hit is None and '{{redirect|' in text:
    _ts = text.split('{{redirect|',1)[-1].split('}}',1)[0].split('|')
    hits = [x for x in keywords if len([y for y in _ts if x in y])>0]
    hit = None if len(hits)==0 else random.choice(hits)
  if hit is None and '{{Redirect|' in text:
    _ts = text.split('{{Redirect|',1)[-1].split('}}',1)[0].split('|')
    hits = [x for x in keywords if len([y for y in _ts if x in y])>0]
    hit = None if len(hits)==0 else random.choice(hits)
  # print(f'hit: {hit}')
  # print()
  
  # カテゴリー
  categories = [x.split(']]',1)[0].split('|',1)[0].strip() for x in text.split('[[Category:')[1:]]
  # print(f'categories: {categories}')
  # print()
  
  # 概要
  summary = text
  # print(f'summary:\n{summary}\n===')
  
  # とりあえず一回短めに本文をとる
  summary = '\n\n'.join(summary.strip().split('\n\n',5)[:-1])
  # print(f'summary:\n{summary}\n===')
  
  # {{.*}} の除去
  # print('remove {{}}')
  while re.search(r'{{(?!.*{{).*?}}', summary):
    summary = re.sub(r'{{(?!.*{{).*?}}', ' ', summary)
  # summary = re.sub(r'{{Maplink(.|\s)*?}}', ' ', summary)
  # summary = re.sub(r'{{ウィキ(.|\s)*?}}', ' ', summary)
  summary = re.sub(r'{{(.|\s)*?}}', ' ', summary)
  
  # [[.*]] の処理
  # _ms = re.search(r'\[\[(.|\s)*?\]\]', summary)
  _ms = re.search(r'\[\[(?!.*(\[\[|:))(.|\s)*?\]\]', summary)
  while _ms:
    _span = _ms.span()
    _m = summary[_span[0]:_span[1]]
    # print(_m)
    _r = _m.split('[[',1)[-1].split(']]',1)[0].split('|',1)[-1]
    # print(_r)
    summary = summary.replace(_m, _r)
    # print(summary)
    # _ms = re.search(r'\[\[(.|\s)*?\]\]', summary)
    _ms = re.search(r'\[\[(?!.*(\[\[|:))(.|\s)*?\]\]', summary)
  # print(f'summary:\n{summary}\n===')
  
  # [[.*:.*]] の除去
  # print('remove [[:]]')
  summary = re.sub(r'\[\[.*:(.|\s)*?\]\]', ' ', summary)
  # summary = re.sub(r'\[\[画像(.|\s)*?\]\]', ' ', summary)
  # print(f'summary:\n{summary}\n===')
  
  # <ref>.*</ref> の除去
  # print('remove <ref>')
  # summary = re.sub('<ref(.|\s)*?</ref>', ' ', summary)
  summary = re.sub(r'<ref>(.|\s)*?</ref>', ' ', summary)
  # summary = re.sub(r'<ref (.|\s)*?</ref>', ' ', summary)
  # print(f'summary:\n{summary}\n===')
  
  # <!--.*--> の除去
  # print('remove <!-- -->')
  summary = re.sub(r'<!--.*?-->', ' ', summary)
  # print(f'summary:\n{summary}\n===')
  
  # ''' の除去
  # print('remove \'\'\'')
  summary = summary.replace('\'\'\'', '')
  
  summary = summary.strip().split('\n\n',1)[0]
  # summary = summary.replace('\n', ' ')
  # print(f'summary:\n{summary}\n===')
  
  summary = re.sub(r'\s+', ' ', summary).strip()
  # print(f'summary:\n{summary}\n===')
  
  # 記事のURL
  wurl = f'https://ja.wikipedia.org/wiki/{title}'
  
  # 記事の不十分さ
  wiki_not_enough = False
  if '{{出典の明記|' in text:
    wiki_not_enough = True
  
  wiki_data = {
    'hit': hit,
    'title': title,
    'text': text,
    'categories': categories,
    'summary': summary,
    'url': wurl,
    'not_enough': wiki_not_enough,
  }
  return wiki_data

def access_db_to_data(keywords, debug=False):
  '''
  入力から返答を作成
  input:
    - keywords: キーワードリスト (unicode)
    - debug: 中間結果を表示するかどうか (bool)
  output: wikipediaページデータ (dict) のリスト
  '''
  
  # キーワード
  if debug:
    print('keywords: {}'.format(keywords))
    print()
  
  # DBのクエリ文 (URL) を作成
  url = make_url(keywords)
  if debug:
    print('url: {}'.format(url))
    print()
  
  # DBにクエリを投げる
  results = db_access(url)
  if debug:
    print('results: {}'.format(json.dumps(results, indent=2, ensure_ascii=False)))
    # print(type(results))
    print()
  
  # wikipediaページデータ抽出結果
  wiki_data = [parse_result(keywords, x) for x in results]
  if debug:
    print('wiki_data:')
    for _d in wiki_data:
      print(json.dumps(_d, indent=2, ensure_ascii=False))
  
  return wiki_data

if __name__ == '__main__':
  # print(sys.argv)
  keywords = sys.argv[1:]
  access_db_to_data(keywords, debug=True)
  
