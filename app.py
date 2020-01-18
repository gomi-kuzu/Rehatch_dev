from flask import Flask, render_template, request, abort
import os
import slack
from urllib import request as req
import random
import xmltodict
import urllib.parse
import requests
import json
import urllib.request
import util_refa


app = Flask(__name__)

client = slack.WebClient(token=os.environ['SLACK_API_TOKEN'])
root_url = "https://crd.ndl.go.jp/api/refsearch"

##### LINE bot SETTING(START)
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

line_channel_access_token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
line_channel_secret = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(line_channel_access_token)
# handler = WebhookHandler(LINE_CHANNEL_SECRET)
parser = WebhookParser(line_channel_secret)

##### LINE bot SETTING(END)


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



# def make_url(key_word,serch_type = "question"):
#     s = ""
#     for i,w in enumerate(key_word.split(" and ")):
#         if i !=0:
#             s += " and " 
#         s += "{} any {}".format(serch_type,w)
#     s_quote = urllib.parse.quote(s)
#     url = "{}?type=reference&query={}".format(root_url,s_quote)
#     return url

# def make_response(url,name):
#     reps = []
#     req = requests.get(url)
#     dict = xmltodict.parse(req.text)
#     if 'result' in dict['result_set']:
#         dict = dict['result_set']['result']
#         if isinstance(dict, list):
#             dict = random.choice(dict)
#         question = dict['reference']['question'].replace("\n","")
#         link = dict['reference']['url']

#         reps += ['{} のあたりにいるんだね！'.format(name)]
#         reps += ['そこについては、「{}」という質問を図書館に投げかけた人がいるみたいだよ。'.format(question)]
#         reps += ['もっと詳しく知りたいならリンク先をみてみてね！']

#     else:
#         link = False
#         reps += ['ちょっとわからないや。どこか地名を教えて。']

#     return reps,link


# def send_to_slack(send_text,channel_name= "#botデバッグ用"):
#   response = client.chat_postMessage(channel=channel_name, text=send_text,icon_emoji = ":rehatch_1:",username="れはっち" )


def record_log_to_kintone( source, send_text, sender ):
  
  url = os.environ['KINTONE_URL']
  headers = {
    "X-Cybozu-API-Token": os.environ['CYBOZU_LOG_DB_API_TOKEN'],
    "Content-type": "application/json",
  }
  data = {
    "app": os.environ['CYBOZU_LOG_DB_APP_ID'],
    "record": {
      "type": {
        "value": source
      },
      "questioner": {
        "value": sender
        },
      "log": {
        "value": send_text
      },
    }
  }
  req = urllib.request.Request(url, json.dumps(data).encode(), headers)
  with urllib.request.urlopen(req) as res:
    body = res.read()
    # print("body=\n" + body.hex())
  
  
  
  
@app.route('/')
def hello():

  name = "hello"
  return name

#for robophone
@app.route('/api/command/reference_talk', methods=['GET'])
def recieve_get():
  query = request.args.get('content')
  
  # url = make_url(query)
  # reps,link_url = make_response(url,query)
  # for r in reps:
  #   print('> {}'.format(r))
  # if link_url:
  #   send_to_slack(link_url)
  #   reps += ['スラックに送ったよ！']

  reqs = util_refa._turn(query)
    
  message = []
  for r in reqs:
    if "v" in r:
      sent = r["v"]
      print('> {}'.format(sent))
      message.append(sent)
  
    
  return ''.join(message)

#for Slack
# @app.route('/api/command/reference_talk/from_slack', methods=['POST'])
# def recieve_post_slack():
#   query = request.form['text']
#   send_user = request.form['user_name']

#   print(request.form)
#   print('query: {}'.format(query))

#   url = make_url(query)
#   reps,link_url = make_response(url,query)
#   for r in reps:
#     print('> {}'.format(r))
  
  
#   if link_url:
#     send_to_slack('{}さんは'.format(send_user) + ''.join(reps))
#     send_to_slack(link_url)
#   else:
#     send_to_slack(''.join(reps))
    
#   return ''


######## LINE bot (START) ########
# https://github.com/line/line-bot-sdk-python/tree/master/examples/flask-echo

@app.route("/line_callback", methods=['POST'])
def callback():
  # get X-Line-Signature header value
  signature = request.headers['X-Line-Signature']
  
  print( "start line callback" )

  # get request body as text
  body = request.get_data(as_text=True)


  # parse webhook body
  try:
    print("Request body: " + body)
    events = parser.parse(body, signature)
  except InvalidSignatureError:
    abort(400)

  # if event is MessageEvent and message is TextMessage, then get text
  for event in events:
    if not isinstance(event, MessageEvent):
      continue
    if not isinstance(event.message, TextMessage):
      continue

    if event.reply_token == "00000000000000000000000000000000" or event.reply_token == "ffffffffffffffffffffffffffffffff":
      print( " from system message. so do not to do.\n ")
      return 'OK'
    
    #reply LINE bot
    query = event.message.text
    #url = make_url(query)
    reqs = util_refa._turn(query)
    #reqs,link_url = make_response(url,query)
    
    message = []
    for r in reqs:
      if "t" in r:
        sent = r["t"]
        print('> {}'.format(sent))
        message.append(sent)
  
    # if link_url:
    #   reply_message = ''.join(reps) + "\n" + link_url
    # else:
    #   reply_message = ''.join(reps)
    
    reply_message = ''.join(message)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage( text=reply_message )
      )
    
    record_log_to_kintone( "LINE_BOT", event.message.text, event.source.user_id )     #event.source.userIdで無い理由は不明
    
    
    #line_bot_api.reply_message(
    #  event.reply_token,
    #  TextSendMessage(text=event.message.text)
    #)
    print("line reply end.")

  return 'OK'
  

######## LINE bot (END) ########


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
