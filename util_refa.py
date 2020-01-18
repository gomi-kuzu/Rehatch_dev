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

def get_char_type(c):
  '''
  文字タイプ判定
  '''
  if re.match('[\u3041-\u309F]', c):
    return 'hira' # ひらがな
  elif re.match('[\u30A1-\u30FF]', c):
    return 'kata' # カタカナ
  elif re.match('[\u2E80-\u2FDF\u3005-\u3007\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U0002EBEF]', c):
    return 'kanji' # 漢字
  else:
    return 'other' # その他

def get_keywords(text):
  '''
  ベタテキストから、検索キーワード (地名) を抜き出す
  '''
  ret = []
  text = text.strip()
  
  if len(ret)==0:
    # for text input
    # 括弧で括られた文字列をキーワードとする
    brackets = [('"', '"'), ('「','」')]
    for b in brackets:
      _text = text
      while b[0] in _text and b[1] in _text:
        _text = _text.split(b[0],1)[-1]
        if b[1] in _text:
          _t,_text = _text.split(b[1],1)
          if b[0] in _t:
            _t = _t.split(b[0],1)[-1]
          _t = _t.strip()
          if len(_t)>1 and len(_t)<len(text):
            ret += [_t]
  
  if len(ret)==0:
    # for voice input
    # 'という'、'ていう'をヒントにキーワード化
    _t = text
    _t = _t.split('という',1)[0]
    _t = _t.split('とゆう',1)[0]
    _t = _t.split('てゆう',1)[0]
    _t = _t.split('ていう',1)[0]
    _t = _t.strip('っ')
    _t = _t.strip()
    if len(_t)>1 and len(_t)<len(text):
      ret += [_t]
  
  if len(ret)==0:
    # かな、カナ、漢字の切れ目でキーワードにする
    _t = ''
    for c in text:
      if len(_t)>0:
        t0 = get_char_type(_t[-1])
        t1 = get_char_type(c)
        if 'other' not in [t0, t1] and t0!=t1:
          # 極端に短いものを削除
          if len(_t)>1:
            ret += [_t]
          _t = ''
      _t += c
    if len(_t)>1 and len(_t)<len(text):
      ret += [_t]
  
  # 重複削除
  ret = list(set(ret))
  
  # キーワードが何も得られなかったとき、
  # しょうがないので元のベタテキストをキーボードにする
  if len(ret)==0:
    ret = [text]
  
  return ret

def make_url_2(keywords, serch_type="question"):
  '''
  レファレンス協同DBに投げるクエリ作成
  '''
  root_url = "https://crd.ndl.go.jp/api/refsearch"
  query = '{} any {}'.format(serch_type, ' '.join(keywords))
  url = '{}?type=reference&query={}'.format(root_url,
                                            urllib.parse.quote(query))
  return url

def db_access(query):
  '''
  レファレンス協同DBにクエリ投げる
  '''
  results = requests.get(query)
  results = xmltodict.parse(results.text)
  results = results['result_set']
  if 'result' in results:
    return results['result']
  else:
    return []

def make_wait_res():
  '''
  待ち状態のメッセージを適当に返す
  {'t':TEXT_MESSAGE, 'v':VOICE_MESSAGE}
  '''
  cnads = [
    {
      't':'やあ! レファレンス共同データベース のマスコット。れはっち だよ!',
      'v':'やあ! レファレンス共同データベース のマスコット。れはっち だよ!'
      },
    {
      't':'全国の図書館に寄せられた疑問を紹介するよ。',
      'v':'全国の図書館に寄せられた疑問を紹介するよ。'
      },
    {
      't':'気になっている場所はあるかな?',
      'v':'気になっている場所はあるかな?'
      },
    {
      't':'今はどこにいるのかな?',
      'v':'今はどこにいるのかな?'
      },
  ]
  ret = random.choice(cnads)
  return ret

def make_noresult_res():
  '''
  検索結果が見つからないときのメッセージを適当に返す
  {'t':TEXT_MESSAGE, 'v':VOICE_MESSAGE}
  '''
  cnads = [
    {
      't':'その場所についてはよく知らないや。',
      'v':'その場所についてはよく知らないや。'
      },
    {
      't':'ごめんね。 ちょっとその場所についてはよく分からないや。',
      'v':'ごめんね。 ちょっとその場所についてはよく分からないや。'
      },
    {
      't':'んー。 よくわからないなあ。 別の言い方をしてみて。',
      'v':'んー。 よくわからないなあ。 別の言い方をしてみて。',
      },
    {
      't':'よくわからないなあ。地名を 「○○」 というふうに書いてくれると分かりやすいかも。',
      'v':'よくわからないなあ。 まるまる という場所 という言い方をしてくれると分かりやすいかも。'
      },
  ]
  ret = random.choice(cnads)
  return ret

def make_quote(text, length=40):
  '''
  引用文を作る
  length: 引用文の幅
  '''
  ret = []
  for l in range(0, len(text), length):
    ret += ['    '+text[l:l+length]]
  ret = '\n'.join(ret)
  return ret

# https://qiita.com/mynkit/items/d6714b659a9f595bcac8
def delete_brackets(s):
    """
    括弧と括弧内文字列を削除
    """
    """ brackets to zenkaku """
    table = {
        "(": "（",
        ")": "）",
        "<": "＜",
        ">": "＞",
        "{": "｛",
        "}": "｝",
        "[": "［",
        "]": "］"
    }
    for key in table.keys():
        s = s.replace(key, table[key])
    """ delete zenkaku_brackets """
    l = ['（[^（|^）]*）', '【[^【|^】]*】', '＜[^＜|^＞]*＞', '［[^［|^］]*］',
         '「[^「|^」]*」', '｛[^｛|^｝]*｝', '〔[^〔|^〕]*〕', '〈[^〈|^〉]*〉']
    for l_ in l:
        s = re.sub(l_, "", s)
    """ recursive processing """
    return delete_brackets(s) if sum([1 if re.search(l_, s) else 0 for l_ in l]) > 0 else s

def make_voice(text, max_length=100):
  '''
  ボイスメッセージ用に文章をトリミング
  '''
  ret = re.sub(r"\s", "", text)
  # URLの除去
  ret = re.sub(r"(https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+$,%#]+)", "", ret)
  # 括弧の除去
  ret = delete_brackets(ret)
  
  if len(ret)>max_length:
    # 長すぎる質問を適当なところでカット
    _ret = ''
    _buf = ''
    for c in ret:
      _buf += c
      if c in [
        '。', '？',
        '.', '?',
        ]:
        if len(_ret+_buf)>max_length:
          ret = _ret
          break
        else:
          _ret += _buf
        _buf = ''
  return ret

def make_response_2(keywords, results):
  '''
  キーワードと検索結果から、れはっちの返答を作る
  {'t':TEXT_MESSAGE, 'v':VOICE_MESSAGE}
  '''
  
  # 検索結果がないとき
  if len(results)==0:
    return [make_noresult_res()]
  
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
  question = re.sub(r"\s", "", result['reference']['question']).strip()
  # 回答
  answer = re.sub("\s", "", result['reference']['answer']).strip()
  # 回答図書館
  lib = result['reference']['system']['lib-name']
  # 質問のurl
  qurl = re.sub("\s", "", result['reference']['url']).strip()
  
  ret = []
  
  # 地名に関する反応
  if hit is not None:
    ret += [random.choice([
      {
        't': '{} にいるんだね!'.format(hit),
        'v': '{} にいるんだね!'.format(hit),
        },
      {
        't': '{} のあたりにいるのかな。'.format(hit),
        'v': '{} のあたりにいるのかな。'.format(hit),
        },
      ])]
  else:
    hits = [x for x in keywords if x in question]
    hit = None if len(hits)==0 else random.choice(hits)
  
  # レファレンスに関するメッセージ
  # for text
  if hit is not None:
    ret += [random.choice([
      {'t': '{} といえば、\n{}\nという質問をした人がいるみたいだよ。'.format(hit, make_quote(question))},
      {'t': '{} については、\n{}\nという質問をした人がいるみたいだよ。'.format(hit, make_quote(question))},
      {'t': '{} については、\n{}\nということが気になっている人がいるみたいだよ。'.format(hit, make_quote(question))},
      ])]
  else:
    ret += [random.choice([
      {'t': 'ふむふむ。そういえば、\n{}\nという質問をした人がいるみたいだよ。'.format(make_quote(question))},
      {'t': 'ふむふむ。そういえば、\n{}\nということが気になっている人がいるみたいだよ。'.format(make_quote(question))},
      ])]
  ret += [random.choice([
    {'t': 'これには、{} の職員さんが答えてくれたんだ。\nそれによると、\n{}\nなんだって。'.format(lib, make_quote(answer))},
    {'t': 'この質問には、{} の職員さんが答えてくれたんだ。\nそれによると、\n{}\nなんだって。'.format(lib, make_quote(answer))},
    ])]
  ret += [random.choice([
    {'t': 'おもしろいね!'},
    {'t': '興味深いね!'},
    {'t': 'おどろきだね!'},
    ])]
  ret += [{'t': 'もっと詳しく知りたいならリンク先をみてみてね!'}]
  
  # レファレンスに関するメッセージ
  # for voice
  if hit is not None:
    ret += [random.choice([
      {'v': '{} といえば、 {} ということを質問をした人がいるみたいだよ。'.format(hit, make_voice(question))},
      {'v': '{} については、 {} という質問をした人がいるみたいだよ。'.format(hit, make_voice(question))},
      {'v': '{} といえば、 {} ということが気になっている人がいるみたいだよ。'.format(hit, make_voice(question))},
      ])]
  else:
    ret += [random.choice([
      {'v': 'ふむふむ。そういえば、 {} という質問をした人がいるみたいだよ。'.format(make_voice(question))},
      {'v': 'ふむふむ。そういえば、 {} ということが気になっている人がいるみたいだよ。'.format(make_voice(question))},
      ])]
  ret += [random.choice([
    {'v': 'これには、{} の職員さんが答えてくれたんだ。'.format(make_voice(lib))},
    {'v': 'この質問には、{} の職員さんが答えてくれたんだ。'.format(make_voice(lib))},
    ])]
  ret += [{'v': '回答についてはチャットに送ったリンク先をみてみてね!'}]
  
  ret += [
    {
      't': '質問についてのリンクだよ!\n{}'.format(qurl),
      'v': '質問についてのリンクだよ!\n{}'.format(qurl)
      }
    ]
  
  return ret

def _turn(text, debug=False):
  '''
  入力から返答を作成
  input:
    - text: ユーザ入力文 (unicode)
    - debug: 中間結果を表示するかどうか (bool)
  output: 会話文のリスト [文, 文, ...]
    - 文: dict. key='t' or 'v'. val=返答文.
      - 't': text. text modeのみの返答
      - 'v': voice. voice modeのみの返答
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
  
  # DBのクエリ文 (URL) を作成
  url = make_url_2(keywords)
  if debug:
    print('url: {}'.format(url))
    print()
  
  # DBにクエリを投げる
  results = db_access(url)
  if debug:
    print('results: {}'.format(json.dumps(results, indent=2, ensure_ascii=False)))
    print()
  
  # テキストチャット、ボイスチャット 共通の返答を作成
  res = make_response_2(keywords, results)
  if debug:
    for r in res:
      print(r)
    print()
  
  return res

def dev_exec(mode='t', debug=False):
  '''
  テスト
  input:
    - mode: れはっちのモード. 't'=text mode or 'v'=voice mode.
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
    res = _turn(in_text)
    
    print('れはっち >')
    for r in res:
      if mode in r:
        print('    '+r[mode].replace('\n', '\n    ')) # 適当にインデントつけて表示
  
  return

if __name__ == '__main__':
  mode = 't' if len(sys.argv)<2 else sys.argv[1]
  dev_exec(mode)
  
