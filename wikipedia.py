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

from text_utils import shorten_text, make_voice
import message

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

def make_response(keywords, results):
  '''
  キーワードと検索結果から、れはっちの返答を作る
  {'t':TEXT_MESSAGE, 'v':VOICE_MESSAGE, 'l':URL}
  '''
  
  # 検索結果がないとき
  if len(results)==0:
    ret = [random.choice([
      {
        't': 'まだWikipediaには、きみが気になってることは書かれていないみたい。もしきみが何か知っているなら、記事を書いてみない？',
        'v': 'まだWikipediaには、きみが気になってることは書かれていないみたい。もしきみが何か知っているなら、記事を書いてみない？',
        },
      {
        't': 'わあー！きみが気になっていることは、まだWikipediaに書かれていないみたい。これはきみが記事を書くチャンスだよ！',
        'v': 'わあー！きみが気になっていることは、まだWikipediaに書かれていないみたい。これはきみが記事を書くチャンスだよ！',
        },
      ])]
    return ret
  
  # 検索結果を一つ選択
  result = random.choice(results)
  # print('result: {}'.format(json.dumps(result, indent=2, ensure_ascii=False)))
  
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
  categories = [x.split(']]',1)[0].strip() for x in text.split('[[Category:')[1:]]
  # print(f'categories: {categories}')
  # print()
  
  # 概要
  summary = text
  # print(f'summary:\n{summary}\n===')
  
  # {{.*}} の除去
  while re.search(r'{{(?!.*{{).*?}}', summary):
    summary = re.sub(r'{{(?!.*{{).*?}}', ' ', summary)
  # summary = re.sub(r'{{Maplink(.|\s)*?}}', ' ', summary)
  # summary = re.sub(r'{{ウィキ(.|\s)*?}}', ' ', summary)
  summary = re.sub(r'{{(.|\s)*?}}', ' ', summary)
  
  # [[.*:.*]] の除去
  summary = re.sub(r'\[\[.*:(.|\s)*?\]\]', ' ', summary)
  # summary = re.sub(r'\[\[画像(.|\s)*?\]\]', ' ', summary)
  # print(f'summary:\n{summary}\n===')
  
  # {{.*}} の除去
  while re.search(r'{{(?!.*{{).*?}}', summary):
    summary = re.sub(r'{{(?!.*{{).*?}}', ' ', summary)
  # summary = re.sub(r'{{Maplink(.|\s)*?}}', ' ', summary)
  # summary = re.sub(r'{{ウィキ(.|\s)*?}}', ' ', summary)
  summary = re.sub(r'{{(.|\s)*?}}', ' ', summary)
  
  # [[.*:.*]] の除去
  summary = re.sub(r'\[\[.*:(.|\s)*?\]\]', ' ', summary)
  # summary = re.sub(r'\[\[画像(.|\s)*?\]\]', ' ', summary)
  # print(f'summary:\n{summary}\n===')
  
  # <ref>.*</ref> の除去
  summary = re.sub(r'<ref(.|\s)*?</ref>', ' ', summary)
  # <!--.*--> の除去
  summary = re.sub(r'<!--(.|\s)*?-->', ' ', summary)
  
  # ''' の除去
  summary = summary.replace('\'\'\'', '')
  
  summary = summary.strip().split('\n\n',1)[0]
  # summary = summary.replace('\n', ' ')
  # print(f'summary:\n{summary}\n===')
  
  # [[.*]] の処理
  _ms = re.search(r'\[\[(.|\s)*?\]\]', summary)
  while _ms:
    _span = _ms.span()
    _m = summary[_span[0]:_span[1]]
    # print(_m)
    _r = _m.split('[[',1)[-1].split(']]',1)[0].split('|',1)[-1]
    # print(_r)
    summary = summary.replace(_m, _r)
    # print(summary)
    _ms = re.search(r'\[\[(.|\s)*?\]\]', summary)
  
  summary = re.sub(r'\s+', ' ', summary).strip()
  summary_v = make_voice(summary)
  # print(f'summary:\n{summary}\n===')
  
  # 記事のURL
  wurl = f'https://ja.wikipedia.org/wiki/{title}'
  
  # 記事の不十分さ
  wiki_not_enough = False
  if '{{出典の明記|' in text:
    wiki_not_enough = True
  
  ret = []
  
  # ヒットキーワードについて
  if hit is not None:
    ret += [random.choice([
      {
        't': f'{hit} だね!',
        'v': f'{hit} だね!',
        },
      {
        't': f'{hit} が気になるのかな。',
        'v': f'{hit} が気になるのかな。',
        },
      ])]
  
  # Wikipedia概要について
  if hit is not None:
    ret += [random.choice([
      {
        't': f'Wikipediaによると、{hit} といえば、\n{summary}\nなんだって。',
        'v': f'Wikipediaによると、{hit} といえば、\n{summary_v}\nなんだって。',
        },
      {
        't': f'{hit} については、Wikipediaには、\n{summary}\nとあるね。',
        'v': f'{hit} については、Wikipediaには、\n{summary_v}\nとあるね。',
        },
      ])]
  else:
    ret += [random.choice([
      {
        't': f'そういえば、Wikipediaの記事に、\n{summary}\nというのがあるよ。',
        'v': f'そういえば、Wikipediaの記事に、\n{summary_v}\nというのがあるよ。',
        },
      {
        't': f'ねえねえ。Wikipediaに、\n{summary}\nという記事があるよ。',
        'v': f'ねえねえ。Wikipediaに、\n{summary_v}\nという記事があるよ。',
        },
      ])]
  ret += [{'l': wurl}]
  
  # 記事が不十分なとき
  if wiki_not_enough:
    ret += [random.choice([
      {
        't': 'ふむふむ。この記事はまだ十分でないみたい。もしきみが何か知ってることがあれば書き込んでみようよ。',
        'v': 'ふむふむ。この記事はまだ十分でないみたい。もしきみが何か知ってることがあれば書き込んでみようよ。',
        },
      {
        't': 'ねえねえ。まだこの記事は十分じゃないみたい。きみの知っていることを書き込むチャンスかもしれないよ。',
        'v': 'ねえねえ。まだこの記事は十分じゃないみたい。きみの知っていることを書き込むチャンスかもしれないよ。',
        },
      ])]
  
  return ret

def access_db_to_response(keywords, debug=False):
  '''
  入力から返答を作成
  input:
    - keywords: キーワードリスト (unicode)
    - debug: 中間結果を表示するかどうか (bool)
  output: 会話文のリスト [文, 文, ...]
    - 文: dict. key='t' or 'v'. val=返答文.
      - 't': text. text modeのみの返答
      - 'v': voice. voice modeのみの返答
      - 'l': URL
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
  
  # テキストチャット、ボイスチャット 共通の返答を作成
  res = make_response(keywords, results)
  if debug:
    print('response:')
    for r in res:
      print(r)
    print()
  
  return res

if __name__ == '__main__':
  # print(sys.argv)
  keywords = sys.argv[1:]
  access_db_to_response(keywords, debug=True)
  
