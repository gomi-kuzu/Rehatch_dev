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

from text_utils import get_keywords
from message import make_wait_res, make_noresult_res
import refkyo
import wikipedia

def get_response(text, debug=False):
  '''
  入力から返答を作成
  input:
    - text: ユーザ入力文 (unicode)
    - debug: 中間結果を表示するかどうか (bool)
  output: 会話文のリスト [文, 文, ...]
    - 文: dict. key='t' or 'v'. val=返答文.
      - 't': text. text modeのみの返答
      - 'v': voice. voice modeのみの返答
      - 'l': URL
  '''
  
  # 入力文
  if debug:
    print('text: {}'.format(text))
    print()
  
  # キーワードを抽出
  keywords = get_keywords(text)
  if debug:
    print('keywords: {}'.format(keywords))
    print()
  
  res = []
  
  # wikipediaからレスポンス生成
  res +=  wikipedia.access_db_to_response(keywords, debug=debug)
  # レファ協からレスポンス生成
  res += refkyo.access_db_to_response(keywords, debug=debug)
  
  return res

def dev_exec(mode='t', debug=False):
  '''
  テスト
  input:
    - mode: れはっちのモード. 't'=text mode, 'v'=voice mode, 'l'=URL.
    - debug: 中間結果を表示するかどうか
  '''
  assert mode in ['t', 'v']
  
  print('start れはっち (mode={})'.format('text' if mode=='t' else 'voice'))
  print('debug={}'.format(debug))
  print()
  
  while True:
    # れはっちからの待機文
    print('れはっち > {}'.format(make_wait_res()[mode]))
    
    # 標準入力から文を入力
    in_text = input('YOU > ')
    
    # 入力に対する返答
    res = get_response(in_text)
    
    print('れはっち >')
    for r in res:
      # print(r)
      if mode in r:
        print(r[mode])
      if 'l' in r:
        print(r['l'])
  
  return

def test(text):
  res = get_response(text)
  # mess = []
  # for r in res:
  #   if "v" in r:
  #     mess.append(r["v"])
  #   if "l" in r:
  #     mess.append("\n" + r["l"] + "\n")
  # return ''.join(mess)

  message = []
  links = []
  for r in res:
    if "v" in r:
      sent = r["v"]
      print('> {}'.format(sent))
      message.append(sent)
    elif "l" in r:
      link = r["l"]
      links.append(link)
  return "{}\n{}".format(message[-1],links[-1])

if __name__ == '__main__':
  # mode = 't' if len(sys.argv)<2 else sys.argv[1]
  # dev_exec(mode)
  print(test(sys.argv[1]))
  
  
  
