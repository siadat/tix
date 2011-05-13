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

  @classmethod
  def get_last_regex(self):
    if len(self.regex_patterns) > 0:
      return self.regex_patterns[-1]
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
