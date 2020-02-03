import sys
import argparse
import re
import json
import os
import random
import ftfy

def get_char_type(c):
  '''
  文字タイプ判定
  out: 'hira', 'kata', 'kanji', or 'other'
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
    _t = _t.split('ていう',1)[0]
    _t = _t.split('てゆう',1)[0]
    _t = _t.strip('っ')
    # 'について'をヒントにキーワード化
    _t = _t.split('について',1)[0]
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
  
  # ひらがなのみのキーワードを削除
  _ret = []
  for x in ret:
    if not all(get_char_type(c)=='hira' for c in x):
      _ret += [x]
  ret = _ret
  
  # キーワードが何も得られなかったとき、
  # しょうがないので元のベタテキストをキーボードにする
  if len(ret)==0:
    ret = [text]
  
  return ret

def make_quote(text, length=40, indent='    '):
  '''
  引用文を作る
  length: 引用文の幅
  '''
  ret = []
  for l in range(0, len(text), length):
    ret += [indent+text[l:l+length]]
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

def shorten_text(text, max_length=200):
  '''
  文章を、max_lengthを超えないN文にして、短くする
  '''
  ret = ftfy.fix_text(text)
  if len(ret)>max_length:
    # 長すぎる文を適当なところでカット
    _ret = ''
    _buf = ''
    for c in ret:
      _buf += c
      # if c in ['。', '？', '.', '?']:
      if c in ['。', '？', '\n']:
        if len(_ret+_buf)>max_length:
          ret = _ret
          break
        else:
          _ret += _buf
        _buf = ''
  return ret

def make_voice(text, max_length=100):
  '''
  ボイスメッセージ用に文章をトリミング
  '''
  ret = re.sub(r"\s", "", text)
  # URLの除去
  ret = re.sub(r"(https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+$,%#]+)", "", ret)
  # 括弧の除去
  ret = delete_brackets(ret)
  # 長すぎる質問を適当なところでカット
  ret = shorten_text(ret, max_length=max_length)
  return ret
