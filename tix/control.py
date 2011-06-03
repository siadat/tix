import threading

class Control(object):
  list_visible_index = 0
  tags_visible_index = 0

  LIST_VIEW_FIRSTLINE, LIST_VIEW_FILENAME, = range(2)
  LIST_VIEWS = {
      LIST_VIEW_FIRSTLINE: 'firstline',
      LIST_VIEW_FILENAME: 'filename',
      }
  list_view_mode = 0

  reload_notes = True
  reload_thread_lock = threading.Lock()
  
  regex_patterns = []
  current_regex_index = 0
  file_history = []

  @classmethod
  def get_last_regex(self):
    if len(self.regex_patterns) > 0:
      return self.regex_patterns[-1].value[1:]
    else:
      return ""

class SortMode(object):
  current = 0
  BY_DATE, BY_FILENAME, BY_SHUF = range(3)
  OPTIONS = {
      BY_SHUF: 'random',
      BY_DATE: 'date',
      BY_FILENAME: 'filename',
      }

class TixMode(object):
  current = 0
  LIST, TAGS, EDIT = range(3)
  OPTIONS = {
      LIST: 'list',
      TAGS: 'tags',
      EDIT: 'edit',
      }

class UserMode(object):
  current = 0
  ALL = 'ALL'
  NOTAG = 'NOTAG'
  DEFAULT_MODES = set([ALL, NOTAG])

class History(object):
  def __init__(self, value):
    import time
    self._time = time.strftime("%Y-%m-%d-%H:%M:%S", time.gmtime())
    self._value = value
  @property
  def time(self):
    return self._time
  @property
  def value(self):
    return self._value
  def __str__(self): return "%s %s\n" % (self._time, self._value)

  def append_to_file(self, history_path):
    import utils
    with open(history_path, 'a') as f:
      f.write(str(self))

  @classmethod
  def load_history_from_file(self, history_path):
    import os
    files_list = list()
    if not os.path.exists(history_path):
      return files_list
    for line in open(history_path, 'r'):
      line = line.strip()
      if line:
        timestamp, file_name = line.split(' ', 1)
        h = History(file_name)
        files_list.append(h)
    return files_list

