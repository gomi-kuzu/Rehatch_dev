import util_refa

reqs = util_refa._turn("相撲")

message = []
for r in reqs:
#   print(r)
#   print("===========")
  if "t" in r:
    sent = r['t']
    print('> {}'.format(sent))
    message.append(sent)

print(message)