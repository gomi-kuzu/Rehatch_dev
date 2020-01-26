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

def make_response(keywords, results):
  '''
  キーワードと検索結果から、れはっちの返答を作る
  {'t':TEXT_MESSAGE, 'v':VOICE_MESSAGE, 'l':URL}
  '''
  
  # 検索結果がないとき
  if len(results)==0:
    return [message.make_noresult_res()]
  
  # 検索結果を一つ選択
  result = random.choice(results)
  # print('result: {}'.format(json.dumps(result, indent=2, ensure_ascii=False)))
  
  # ヒットしたキーワード
  hit = None
  if 'keyword' in result['reference']:
    hits = [x for x in keywords
            if len([y for y in result['reference']['keyword'] if x in y])>0]
    hit = None if len(hits)==0 else random.choice(hits)
  # 質問
  question = re.sub(r"\s", " ", result['reference']['question']).strip()
  question_s = shorten_text(question)
  question_v = make_voice(question)
  # 回答
  answer = re.sub("\s", " ", result['reference']['answer']).strip()
  answer_s = shorten_text(answer)
  answer_v = make_voice(answer)
  # 回答図書館
  lib = result['reference']['system']['lib-name']
  lib_v = make_voice(lib)
  # 質問のurl
  qurl = re.sub("\s", " ", result['reference']['url']).strip()
  
  ret = []
  
  # 地名に関する反応
  if hit is not None:
    # ret += [random.choice([
    #   {
    #     't': f'{hit} にいるんだね!',
    #     'v': f'{hit} にいるんだね!',
    #     },
    #   {
    #     't': f'{hit} のあたりにいるのかな。',
    #     'v': f'{hit} のあたりにいるのかな。',
    #     },
    #   ])]
    pass
  else:
    # print(keywords)
    # print(question)
    hits = [x for x in keywords if x in question]
    hit = None if len(hits)==0 else random.choice(hits)
  
  # レファレンスに関するメッセージ
  if hit is not None:
    ret += [random.choice([
      {
        't': f'{hit} といえば、\n{question_s}\nという質問をした人がいるみたいだよ。',
        'v': f'{hit} といえば、 {question_v} ということを質問をした人がいるみたいだよ。',
        },
      {
        't': f'{hit} については、\n{question_s}\nという質問をした人がいるみたいだよ。',
        'v': f'{hit} については、 {question_v} という質問をした人がいるみたいだよ。',
        },
      {
        't': f'{hit} については、\n{question_s}\nということが気になっている人がいるみたいだよ。',
        'v': f'{hit} といえば、 {question_v} ということが気になっている人がいるみたいだよ。',
        },
      ])]
  else:
    ret += [random.choice([
      {
        't': f'ふむふむ。そういえば、\n{question_s}\nという質問をした人がいるみたいだよ。',
        'v': f'ふむふむ。そういえば、 {question_v} という質問をした人がいるみたいだよ。',
        },
      {
        't': f'ふむふむ。そういえば、\n{question_s}\nということが気になっている人がいるみたいだよ。',
        'v': f'ふむふむ。そういえば、 {question_v} ということが気になっている人がいるみたいだよ。',
        },
      ])]
  ret += [random.choice([
    {
      't': f'これには、{lib} の職員さんが答えてくれたんだ。\nそれによると、\n{answer_s}\nなんだって。',
      'v': f'これには、{lib_v} の職員さんが答えてくれたんだ。',
      },
    {
      't': f'この質問には、{lib} の職員さんが答えてくれたんだ。\nそれによると、\n{answer_s}\nなんだって。',
      'v': f'この質問には、{lib_v} の職員さんが答えてくれたんだ。',
      },
    ])]
  ret += [random.choice([
    {
      't': 'おもしろいね!',
      'v': 'おもしろいね!',
      },
    {
      't': '興味深いね!',
      'v': '興味深いね!',
      },
    {
      't': 'おどろきだね!',
      'v': 'おどろきだね!',
      },
    ])]
  ret += [{
    't': 'もっと詳しく知りたいならリンク先をみてみてね!',
    'v': '回答についてはチャットに送ったリンク先をみてみてね!',
    }]
  ret += [{
    't': '質問についてのリンクだよ!',
    'v': '質問についてのリンクだよ!',
    }]
  ret += [{'l': qurl}]
  
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
  
