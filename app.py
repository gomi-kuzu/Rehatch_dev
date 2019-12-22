from flask import Flask, render_template, request
import os
import slack
from urllib import request as req
import random
import xmltodict
import urllib.parse
import requests

app = Flask(__name__)

client = slack.WebClient(token=os.environ['SLACK_API_TOKEN'])
root_url = "https://crd.ndl.go.jp/api/refsearch"


# def get_matchs(query, db):
#     matchs = []
#     for x in db:
#         if len(x)==0:
#             continue
#         if len(x['place_name'])==0:
#             continue
#         if len(x['modern_place_name'])==0:
#             continue
        
#         if x['place_name'] in query or x['modern_place_name'] in query:
#             matchs += [x]
#             print(x)
#     return matchs

# def make_reply(matchs):
#     # 'question', 'referenceDB-URL', 'lib-name', 'place_name', 'modern_place_name', 'reference_materials'
#     reps = []
#     if len(matchs)==0:
#         reps += ['ちょっとわからないや。どこか地名を教えて。']
#     else:
#         m = random.choice(matchs)
#         print(m)
        
#         if len(m['modern_place_name'])>0:
#             reps += ['{} のあたりにいるんだね！'.format(m['modern_place_name'])]
#         if len(m['place_name'])>0 and m['modern_place_name']!=m['place_name']:
#             reps += ['昔の地名や他の言い方だと、その辺は {} と呼ばれていたんだよ。'.format(m['place_name'])]
#         if len(m['reference_materials'])>0:
#             reps += ['{} という本に書かれているんだ。'.format(m['reference_materials'])]
#         if len(m['question'])>0:
#             reps += ['この場所については、{} ということに興味がある人がいるね。'.format(m['question'])]
#         if len(m['referenceDB-URL'])>0:
#             reps += ['もっと詳しく知りたいならリンク先をみてみてね！スラックに送ったよ！']
#     return reps, m['referenceDB-URL']



def make_url(key_word,serch_type = "question"):
    s = ""
    for i,w in enumerate(key_word.split(" and ")):
        if i !=0:
            s += " and " 
        s += "{} any {}".format(serch_type,w)
    s_quote = urllib.parse.quote(s)
    url = "{}?type=reference&query={}".format(root_url,s_quote)
    return url

def make_response(url,name):
    reps = []
    req = requests.get(url)
    dict = xmltodict.parse(req.text)
    if 'result' in dict['result_set']:
        dict = dict['result_set']['result']
        if isinstance(dict, list):
            dict = random.choice(dict)
        question = dict['reference']['question'].replace("\n","")
        link = dict['reference']['url']

        reps += ['{} のあたりにいるんだね！'.format(name)]
        reps += ['そこについては、「{}」という質問を図書館に投げかけた人がいるみたいだよ。'.format(question)]
        reps += ['もっと詳しく知りたいならリンク先をみてみてね！']

    else:
        link = False
        reps += ['ちょっとわからないや。どこか地名を教えて。']

    return reps,link

def send_to_slack(send_text,channel_name= "#botデバッグ用"):
  response = client.chat_postMessage(channel=channel_name, text=send_text,icon_emoji = ":rehatch_1:",username="れはっち" )


@app.route('/')
def hello():

  name = "hello"
  return name

#for robophone
@app.route('/api/command/reference_talk', methods=['GET'])
def recieve_get():
  query = request.args.get('content')
  send_user = request.args.get('user_name')
  print('user_name: {}'.format(user_name))
  print('query: {}'.format(query))

  url = make_url(query)
  reps,link_url = make_response(url,query)
  # for r in reps:
  #   print('> {}'.format(r))
  if link_url:
    send_to_slack(link_url)
    reps += ['スラックに送ったよ！']
    

  return ''.join(reps)

#for Slack
@app.route('/api/command/reference_talk/from_slack', methods=['POST'])
def recieve_post_slack():
  query = request.form['text']

  print('query: {}'.format(query))

  url = make_url(query)
  reps,link_url = make_response(url,query)
  for r in reps:
    print('> {}'.format(r))
  
  send_to_slack(''.join(reps))
  
  if link_url:
    send_to_slack(link_url)

  return ''

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
