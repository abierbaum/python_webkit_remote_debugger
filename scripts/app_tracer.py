#
# Application to connect and record a trace of a webapp
#
import json
import logging
import optparse
import os
import urllib
import urllib2
import re
import socket
import sys
import time
import types

from objects import Bunch

file_dir  = os.path.abspath(os.path.dirname(__file__))
deps_dir  = os.path.abspath(os.path.join(file_dir, '..', 'deps'))

for pdir in ['websocket-client']:
   sys.path.insert(0, os.path.join(deps_dir, pdir))

from websocket import WebSocket, WebSocketApp

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

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
      self.counter  = 0
      self.host     = options.host
      self.port     = options.port
      self.page_num = options.page_num

      self.timeStart = time.mktime(time.localtime())

      self.ws_url = None
      self.ws     = None

      self._requestDetails = {}   # Map of details about a request


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


   def start(self):
      # if ipv6
      if 0:
         ws.io_sock = ws.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
      #ws.connect("ws://localhost:9999/devtools/page/1")
      self.ws_url = "ws://%s:%s/devtools/page/%s" % (self.host, self.port, self.page_num)

      self.ws = WebSocketApp(self.ws_url,
         on_open    = self.onOpen,
         on_message = self.onMessage,
         on_error   = self.onError,
         on_close   = self.onClose)

      self.ws.run_forever()


   def send(self, method, params = None):
      self.counter += 1

      # separators is important, you'll get "Message should be in JSON format." otherwise
      msg_data = {"id": self.counter, "method": method}
      if params is not None:
         msg_data['params'] = params
      message = json.dumps(msg_data, separators=(',', ':'))
      print "> %s" % (message,)
      self.ws.send(message)


   def recv(self):
      result = self.ws.recv()
      print "< %s" % (result,)
      return result


   # ---- PRIMARY CALLBACKS ---- #
   def onOpen(self, ws):
      #self.send('Runtime.evaluate', {'expression': '1+1'})
      #self.send('Runtime.evaluate', {'expression': 'alert("hello from python")'})
      #self.send('Timeline.start', {'maxCallStackDepth': 5})
      self.send('Network.enable')

   def onMessage(self, ws, message):
      # Decode message into a bunch object to make easier to access attributes
      # but store original message so we can get to it
      msg = Bunch.loads(message)
      msg._rawMsg = json.loads(message)

      if hasattr(msg, 'result'):
         self.handleResultMsg(msg)
      elif hasattr(msg, 'method'):
         self.handleMethodMsg(msg)
      else:
         print "UNKNOWN MSG TYPE: "
         self.prettyPrintMsg(msg_data)

   def onError(self, ws, error):
      print "error: ", error

   def onClose(self, ws):
      print "CLOSED"


   # --- Helpers ---- #
   def prettyPrintMsg(self, msg):
      if type(msg) in types.StringTypes:
         msg = json.loads(msg)
      elif type(msg) == Bunch:
         msg = json.loads(msg._rawMsg)

      print json.dumps(msg, sort_keys=True, indent=3)


   # --- MSG Helpers --- #
   def handleResultMsg(self, msg):
      print "RESULT: [%s]" % msg.id
      print json.dumps(msg._rawMsg['result'], sort_keys=True, indent=3)


   def handleMethodMsg(self, msg):
      """
      Try to map method name to a local handler.
      get name as: 'handle' + method in camel case and no .'s
      """
      def replace(match):
         return match.group()[1].upper()

      method         = msg.method
      handler_name   = 'handle' + re.sub('\.\w', replace, method)
      handler_method = getattr(self, handler_name, self.handleNotificationDefault)
      handler_method(msg)


   def handleNotificationDefault(self, msg):
      """ By default just print the method name. """
      print self.getMethodHeader(msg)

   # --- Network Notification Processing --- #
   def handleNetworkDataReceived(self, msg):
      print self.getMethodHeader(msg)
      print "  request: ", self.getRequestSummary(msg)
      print "  dataLen: ", msg.params.dataLength

   def handleNetworkLoadingFailed(self, msg):
      print self.getMethodHeader(msg)
      print "  request: ", self.getRequestSummary(msg)
      print "    error: ", msg.params.errorText

   def handleNetworkLoadingFinished(self, msg):
      print self.getMethodHeader(msg)
      print "  request: ", self.getRequestSummary(msg)

   def handleNetworkRequestServedFromCache(self, msg):
      print self.getMethodHeader(msg)
      print "  request: ", self.getRequestSummary(msg)

   def handleNetworkRequestServedFromMemoryCache(self, msg):
      print self.getMethodHeader(msg)
      print "  request: ", self.getRequestSummary(msg)
      print "      url: ", msg.params.documentURL

   def handleNetworkRequestWillBeSent(self, msg):
      self._requestDetails[msg.params.requestId] = Bunch(requestId = msg.params.requestId,
         request     = msg.params.request,
         loaderId    = msg.params.loaderId,
         documentUrl = msg.params.documentURL,
         startTs     = msg.params.timestamp,
         initiator   = msg.params.initiator,
         stack       = msg.params.stackTrace)

      print self.getMethodHeader(msg)
      print "  request: ", self.getRequestSummary(msg)
      print "      url: ", msg.params.documentURL

   def handleNetworkResponseReceived(self, msg):
      resp = msg.params.response
      print self.getMethodHeader(msg)
      print "    request: ", self.getRequestSummary(msg)
      print "       type: ", msg.params.type
      print "     reused: ", resp.connectionReused
      print "  from disk: ", resp.fromDiskCache
      print "       mime: ", resp.mimeType
      print "     status: [%s] %s" % (resp.status, resp.statusText)


   # ---- Helpers ---- #
   def getMethodHeader(self, msg):
      return "[%s] ==[ %s ]=====" % (self.getTS(msg), msg.method)

   def getRequestSummary(self, msg):
      req_record = self._requestDetails.get(msg.params.requestId, None)
      if req_record:
         return "[%s] %s" % (msg.params.requestId, req_record.request.url)
      else:
         return "[%s] {unknown}" % msg.params.requestId

   def getTS(self, msg):
      """ Returns a timestamp string to use as prefix """
      ts_value = None
      if hasattr(msg, 'params'):
         ts_value = msg.params.get('timestamp', None)

      if ts_value is None:
         return '<nots>'
      else:
         ts_delta = ts_value - self.timeStart
         return "%8.4f" % ts_delta


def main():
   options, file_args = parseOptions()
   app = TracerApp(options)

   # Handle case where there is no page
   if options.page_num is None:
      app.showConnectionList()
   else:
      app.start()


if __name__ == "__main__":
   main()