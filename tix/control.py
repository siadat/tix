import threading

class Control(object):
  list_visible_index = 0

  SORTBY_DATE, SORTBY_FILENAME, SORTBY_SHUF = range(3)
  SORTBYS = {
      SORTBY_SHUF: 'random',
      SORTBY_DATE: 'date',
      SORTBY_FILENAME: 'filename',
      }
  current_sortby = 0


  LIST_VIEW_FIRSTLINE, LIST_VIEW_TAGS, LIST_VIEW_FILENAME = range(3)
  LIST_VIEWS = {
      LIST_VIEW_FIRSTLINE: 'firstline',
      LIST_VIEW_FILENAME: 'filename',
      LIST_VIEW_TAGS: 'tags',
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

class TixMode(object):
  LIST_TIX_MODE, NOTE_TIX_MODE = range(2)
  TIX_MODES = {LIST_TIX_MODE: 'list', NOTE_TIX_MODE: 'note'}
  current_tix_mode = 0

class UserMode(object):
  ALL= 'ALL'
  current_user_mode = 0
