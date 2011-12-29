
import json

class Bunch(object):
   """
   Useful class type that will act as an object that can have any attributes
   assigned to it (or removed).  Provides a dict/object similar in spirit to
   javascript objects.  (also called DumbObject)
   """
   def __init__(self, **kwds):
      self.__dict__.update(kwds)

   def __eq__(self, other):
      return self.__dict__ == other.__dict__

   def get(self, *args, **kwds):
      return self.__dict__.get(*args, **kwds)

   def has_key(self, *args, **kwds):
      return self.__dict__.has_key(*args, **kwds)

   @staticmethod
   def fromDict(srcDict):
      """
      Create a bunch object (or nested set of objects) from
      the given source dictionary.
      """
      ret_obj = Bunch()

      for (k,v) in srcDict.iteritems():
         if isinstance(v, dict):
            v = Bunch.fromDict(v)
         setattr(ret_obj, k, v)
      return ret_obj

   def toDict(self):
      return dict(self.__dict__)

   @staticmethod
   def loads(jsonStr):
      json_obj = json.loads(jsonStr)
      return Bunch.fromDict(json_obj)

