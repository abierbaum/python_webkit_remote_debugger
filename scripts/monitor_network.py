import json
import os
import urllib2
import socket
import sys

file_dir  = os.path.abspath(os.path.dirname(__file__))
deps_dir  = os.path.abspath(os.path.join(file_dir, '..', 'deps'))

for pdir in ['websocket-client']:
   sys.path.insert(0, os.path.join(deps_dir, pdir))

from websocket import WebSocket, WebSocketApp


#
# Start chrome with: google-chrome --remote-debugging-port=9999
#
debug_port = 9999

if len(sys.argv) != 2:
   pages = urllib2.urlopen("http://localhost:%s/json" % debug_port)
   pages_data = json.loads(pages.read())
   for page in pages_data:
      print "Page: ", page.get('title', '')
      print "   url: ", page.get('url', '')
      print "   ws_debug_url: ", page.get('webSocketDebuggerUrl', '')
   sys.exit(1)

page = sys.argv[1]

print "Attempting to open page: %s on localhost:%s" % (page, debug_port)

# if ipv6
if 0:
   ws.io_sock = ws.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
#ws.connect("ws://localhost:9999/devtools/page/1")
ws_url = "ws://localhost:%s/devtools/page/%s" % (debug_port, page)


def on_message(ws, message):
   print "< raw: ", message

def on_error(ws, error):
   print "error: ", error

def on_close(ws):
   print "CLOSED"

def on_open(ws):
   send('Runtime.evaluate', {'expression': '1+1'})
   send('Runtime.evaluate', {'expression': 'alert("hello from python")'})

gCounter = 0

def send(method, params):
   global gCounter
   gCounter += 1
   # separators is important, you'll get "Message should be in JSON format." otherwise
   message = json.dumps({"id": gCounter, "method": method, "params": params}, separators=(',', ':'))
   print "> %s" % (message,)
   ws.send(message)

def recv():
   result = ws.recv()
   print "< %s" % (result,)


ws = WebSocketApp(ws_url,
      on_open    = on_open,
      on_message = on_message,
      on_error   = on_error,
      on_close   = on_close)

ws.run_forever()