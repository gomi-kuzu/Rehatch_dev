import sys
import argparse
import re
import json
import os
import random

from text_utils import get_keywords, shorten_text, make_voice
import refkyo
import wikipedia

def make_wait_res():
  '''
  待ち状態のメッセージを適当に返す
  {'t':TEXT_MESSAGE, 'v':VOICE_MESSAGE}
  '''
  cnads = [
    {
      't':'やあ！レファレンス共同データベース のマスコット。れはっち だよ！',
      'v':'やあ！レファレンス共同データベース のマスコット。 れはっち だよ！'
      },
    {
      't':'全国の図書館に寄せられた疑問を紹介するよ。',
      'v':'全国の図書館に寄せられた疑問を紹介するよ。'
      },
    {
      't':'気になっている場所はあるかな？',
      'v':'気になっている場所はあるかな？'
      },
    {
      't':'今はどこにいるのかな？',
      'v':'今はどこにいるのかな？'
      },
  ]
  ret = random.choice(cnads)
  return ret

# def make_response(keywords, results):
#   '''
#   キーワードと検索結果から、れはっちの返答を作る
#   {'t':TEXT_MESSAGE, 'v':VOICE_MESSAGE, 'l':URL}
#   '''
#   
#   
#   return ret

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

def make_response(keywords, dataset):
  '''
  入力から返答を作成
  input:
    - keywords: キーワードリスト (unicode)
    - dataset: 各種データベースからの抽出データ. {'ref':レファレンスデータ, 'wiki':wikipediaデータ}
  output: 会話文のリスト [文, 文, ...]
    - 文: dict. key='t' or 'v'. val=返答文.
      - 't': text. text modeのみの返答
      - 'v': voice. voice modeのみの返答
      - 'tl': URLがらみのtext返答
      - 'vl': URLがらみのvoice返答
  '''
  
  wikidata = dataset['wiki']
  refdata = dataset['ref']
  # print(f'keywords: {keywords}')
  # print(f'wikidata: {len(wikidata)}')
  # print(f'refdata: {len(refdata)}')
  
  no_wiki = len(wikidata)==0 # wikipediaデータないかあるか
  no_ref = len(refdata)==0 # レファレンスデータないとき
  
  if no_wiki and no_ref:
    # なんにも結果のないとき
    return [make_noresult_res()]
  elif no_wiki and not no_ref:
    ret = []
    # wikipediaデータのないとき
    ret += [random.choice([
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
  else:
    # wikipediaデータあるとき
    wikihits = list(set([x['hit'] for x in wikidata])) # wikipediaでヒットしたクエリ
    refhits = list(set([x['hit'] for x in refdata])) # レファ協でヒットしたクエリ
    hits = list(set([x for x in wikihits+refhits if x in wikihits and x in refhits])) # マージ
    # print(f'wikihits: {wikihits}')
    # print(f'refhits: {refhits}')
    # print(f'hits: {hits}')
    
    hit = random.choice(hits) # ランダムにキーワード決定
    # print(f'hit: {hit}')
    
    # wikidataフィルタリング
    _data = []
    for _d in wikidata:
      if _d['hit']==hit:
        _data += [_d]
    # print(f'wikidata: {len(_data)}')
    # 1こランダムに選択
    wikidat = random.choice(_data)
    
    # レファ協フィルタリング
    _data = []
    for _d in refdata:
      if _d['hit']==hit:
        _data += [_d]
      elif hit in _d['question']: # レファ協は質問からも探す
        _data += [_d]
    # print(f'refdata: {len(_data)}')
    # 1こランダムに選択
    refdat = None if len(_data)==0 else random.choice(_data)
    
    # 発話生成
    ret = []
    
    # wikipedia
    title = wikidat['title']
    summary = wikidat['summary']
    wurl = wikidat['url']
    wiki_not_enough = wikidat['not_enough']
    title_v = make_voice(title)
    summary_v = make_voice(summary)
    
    # wikipedia: ヒットキーワードについて
    if hit is not None:
      ret += [random.choice([
        {
          't': f'{hit} だね！',
          'v': f'{hit} だね！',
          },
        {
          't': f'{hit} が気になるのかな。',
          'v': f'{hit} が気になるのかな。',
          },
        ])]
    # wikipedia: 概要について
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
      # wikipedia: ページのURL
      ret += [{
        'tl': wurl,
        'vl': f'{hit} に関するWikipedia記事のリンクだよ！\n{wurl}',
        }]
    else:
      ret += [random.choice([
        {
          't': f'そういえば、Wikipediaの記事に {title} というのがあって、\n{summary}\nなんだって。',
          'v': f'そういえば、Wikipediaの記事に {title_v} というのがあって、\n{summary_v}\nなんだって。',
          },
        {
          't': f'ねえねえ。Wikipediaに {title} についての記事があって、\n{summary}\nと書かれているね。',
          'v': f'ねえねえ。Wikipediaに {title_v} についての記事があって、\n{summary_v}\nと書かれているね。',
          },
        ])]
      # wikipedia: ページのURL
      ret += [{
        'tl': wurl,
        'vl': f'{title} についてのWikipedia記事のリンクだよ！\n{wurl}',
        }]
    
    # wikipedia: 記事が不十分なとき
    if wiki_not_enough:
      ret += [random.choice([
        {
          't': 'おや？ この記事はまだ十分でないみたい。もしきみが何か知ってることがあれば書き込んでみようよ。',
          'v': 'おや？ この記事はまだ十分でないみたい。もしきみが何か知ってることがあれば書き込んでみようよ。',
          },
        {
          't': 'ねえねえ。まだこの記事は十分じゃないみたい。きみの知っていることを書き込むチャンスかもしれないよ。',
          'v': 'ねえねえ。まだこの記事は十分じゃないみたい。きみの知っていることを書き込むチャンスかもしれないよ。',
          },
        ])]
    
    # レファレンスデータ
    if refdat:
      question = refdat['question']
      answer = refdat['answer']
      lib = refdat['lib']
      qurl = refdat['url']
      question_s = shorten_text(question)
      question_v = make_voice(question)
      answer_s = shorten_text(answer)
      answer_v = make_voice(answer)
      lib_v = make_voice(lib)
      
      # レファレンス: 質問について
      if refdat['hit']==hit:
        ret += [random.choice([
          {
            't': 'それとね。',
            'v': 'それとね。',
            },
          {
            't': 'あとねえ。',
            'v': 'あとねえ。',
            },
          ])]
        ret += [random.choice([
          {
            't': f'{hit} といえば、\n{question_s}\nという質問を図書館にした人がいるみたいだよ。',
            'v': f'{hit} といえば、 {question_v} という質問を図書館にした人がいるみたいだよ。',
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
      # レファレンス: 図書館、回答について
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
      # レファレンス: 感想
      ret += [random.choice([
        {
          't': 'おもしろいね！',
          'v': 'おもしろいね！',
          },
        {
          't': '興味深いね！',
          'v': '興味深いね！',
          },
        {
          't': 'おどろきだね！',
          'v': 'おどろきだね！',
          },
        ])]
      # レファレンス: URL
      ret += [{
        't': 'もっと詳しく知りたいならレファレンス協同データベースをみてみてね！',
        'v': '回答についてはレファ協データベースをみてみてね！リンクをチャットに送ったよ！',
        }]
      ret += [{
        'tl': f'質問についてのリンクだよ！\n{qurl}',
        'vl': f'質問についてのリンクだよ！\n{qurl}',
        }]
      
    return ret
  
  return

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
      - 'tl': URLがらみのtext返答
      - 'vl': URLがらみのvoice返答
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
  
  # 各種データベースからデータ抽出
  dataset = {}
  dataset['wiki'] = wikipedia.access_db_to_data(keywords)
  dataset['ref'] = refkyo.access_db_to_data(keywords)
  
  # データもとにレスポンス作成
  res = make_response(keywords, dataset)
  
  return res

def test(text):
  res = get_response(text)
  for r in res:
    print(r)
  return

if __name__ == '__main__':
  # mode = 't' if len(sys.argv)<2 else sys.argv[1]
  # dev_exec(mode)
  test(sys.argv[1])

