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
  レファレンス協同DBに投げるクエリ作成
  '''
  root_url = "https://crd.ndl.go.jp/api/refsearch"
  query = '{} any {}'.format(serch_type, ' '.join(keywords))
  url = '{}?type=reference&query={}'.format(
    root_url, urllib.parse.quote(query))
  return url

def db_access(query):
  '''
  レファレンス協同DBにクエリ投げる
  '''
  results = requests.get(query)
  results = xmltodict.parse(results.text)
  # print(results)
  results = results['result_set']
  if 'result' in results:
    ret = results['result']
    if isinstance(ret, list):
      return ret
    else:
      return [ret]
  else:
    return []

def parse_result(keywords, result):
  '''
  クエリレスポンスをパースしてほしいデータを抽出
  input:
    - keywords: キーワードのリスト
    - result: 検索結果
  output: 辞書データ
  '''
  
  # ヒットしたキーワード
  hit = None
  if 'keyword' in result['reference']:
    _kws = [] if result['reference']['keyword'] is None else result['reference']['keyword']
    hits = [x for x in keywords
            if len([y for y in _kws if x in y])>0]
    hit = None if len(hits)==0 else random.choice(hits)
  # 質問
  question = re.sub(r"\s", " ", result['reference']['question']).strip()
  # 回答
  answer = re.sub("\s", " ", result['reference']['answer']).strip()
  # 回答図書館
  lib = result['reference']['system']['lib-name']
  # 質問のurl
  qurl = re.sub("\s", " ", result['reference']['url']).strip()
  
  ref_data = {
    'hit': hit,
    'question': question,
    'answer': answer,
    'lib': lib,
    'url': qurl,
  }
  return ref_data

def access_db_to_data(keywords, debug=False):
  '''
  入力から返答を作成
  input:
    - keywords: キーワードリスト (unicode)
    - debug: 中間結果を表示するかどうか (bool)
  output: レファレンス事例ページデータ (dict) のリスト
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
  
  # レファレンスからデータ抽出
  ref_data = [parse_result(keywords, x) for x in results]
  if debug:
    print('ref_data:')
    for _d in ref_data:
      print(json.dumps(_d, indent=2, ensure_ascii=False))
  
  return ref_data

if __name__ == '__main__':
  # print(sys.argv)
  keywords = sys.argv[1:]
  access_db_to_data(keywords, debug=True)
  
