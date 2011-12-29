#
# Application to connect and record a trace of a webapp
#
import json
import optparse
import os
import urllib
import urllib2
import socket
import sys

file_dir  = os.path.abspath(os.path.dirname(__file__))
deps_dir  = os.path.abspath(os.path.join(file_dir, '..', 'deps'))

for pdir in ['websocket-client']:
   sys.path.insert(0, os.path.join(deps_dir, pdir))

from websocket import WebSocket, WebSocketApp


def parseOptions():
   usage = "%prog [options] page_num"
   epilog = "Note: run with no page num to see list of potential pages"

   parser = optparse.OptionParser(usage=usage, epilog=epilog)
   parser.add_option("--host", default="localhost",
                     help = "The host to connect to. [%default]")
   parser.add_option("--port", type="int", default=9999,
                      help = "The port the remote debugger is running on. [%default]")

   (options, args) = parser.parse_args()
   options.page_num = None
   if len(args) > 0:
      options.page_num = int(args[0])

   return (options, args)


class TracerApp(object):
   """
   Main tracer application.
   """
   def __init__(self, options):
      self.host     = options.host
      self.port     = options.port
      self.page_num = options.page_num

   def showConnectionList(self):
      """
      Print out list of possible debugger connections
      """
      pages_url  = "http://%s:%s/json" % (self.host, self.port)
      pages      = urllib2.urlopen(pages_url)
      pages_data = json.loads(pages.read())
      for page in pages_data:
         print "----------------------------------------------------------"
         print "Page: ", page.get('title', '')
         print "   url: ", page.get('url', '')
         print "   ws_debug_url: ", page.get('webSocketDebuggerUrl', '')

   def other(self):
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
         #send('Runtime.evaluate', {'expression': '1+1'})
         #send('Runtime.evaluate', {'expression': 'alert("hello from python")'})
         #send('Timeline.start', {'maxCallStackDepth': 5})
         send('Network.enable')

      gCounter = 0

      def send(method, params = None):
         global gCounter
         gCounter += 1
         # separators is important, you'll get "Message should be in JSON format." otherwise
         msg_data = {"id": gCounter, "method": method}
         if params is not None:
            msg_data['params'] = params
         message = json.dumps(msg_data, separators=(',', ':'))
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


def main():
   options, file_args = parseOptions()
   app = TracerApp(options)

   # Handle case where there is no page
   if options.page_num is None:
      app.showConnectionList()


if __name__ == "__main__":
   main()