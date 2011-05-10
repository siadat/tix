import os
import re
import utils
import collections
from control import UserMode

class Note(object):
  """The structure used to store all information for each note file."""
  def __init__(self, filename, path, text):
    self.is_shown = False
    self.text = text

    self.filename = filename
    self.path = path

    self.id = None
    self.is_todo = False
    self.first_line = ""

    #self.modes = set()
    self.modes = utils.get_all_tags(self.text)

  def fullpath(self):
    return os.path.join(self.path, self.filename)

  def is_a_match(self, regex, flags = 0):
    try:
      if regex.strip() is '': return True
      regex = regex.replace('#', '\\#')
      return re.search(regex, self.path + self.filename + self.text,
          re.MULTILINE | re.DOTALL | re.VERBOSE | flags)
    except re.error:
      return True

  def process_meta(self, id):
    self.id = id
    self.is_todo = self.is_a_match(r'\b(TODO|DEADLINE)\b[^\'"`]')
    self.is_someday = self.is_a_match(r'\b(SOMEDAY)\b[^\'"`]')
    self.first_line = utils.get_first_line(self.text)
    #self.nbr_of_lines = utils.get_number_of_lines(self.text, 80)

  def is_search_match(self, regex):
    return self.is_a_match(regex, re.IGNORECASE)

  def visible(self, visibility):
    self.is_shown = visibility


class NoteList(collections.MutableSequence):
  """Holds all loaded notes."""
  def __init__(self):
    self.list = list()
    self.oktype = Note
    self._modes_set = set([UserMode.ALL])
    #self.current_index = 0
    #self.current_user_mode = 0

  def reset(self):
    del self.list[:]

  def check(self, v):
    if not isinstance(v, self.oktype):
      raise TypeError, v

  def sort_by_modification_date(self):
    self.list = sorted(self.list,
        key=lambda note: utils.get_modification_date(note.fullpath()),
        reverse=True)

  def sort_by_filename(self):
    self.list = sorted(self.list,
        key=lambda note: note.fullpath(),
        reverse=True)

  def has_note(self):
    return self.list != []

  def __setitem__(self, i, v):
    self.check(v)
    self.list[i] = v

  def extend(self, values):
    if not isinstance(values, NoteList):
      raise TypeError, values

    for v in values:
      self.list.append(v)
      self._modes_set = self._modes_set.union(v.modes)
    #self.current_user_mode += len(values)

  def insert(self, i, v):
    self.check(v)
    self._modes_set = self._modes_set.union(v.modes)
    self.list.insert(i, v)
    #self.current_user_mode += 1

  def modes(self):
    def comp(a, b):
      v1 = a.lower().replace('#', 'z')
      v2 = b.lower().replace('#', 'z')
      return cmp(v1, v2)
    return sorted(list(self._modes_set), cmp=comp)

  def get_visible(self, key):
    index = 0
    for i in self.list:
      if i.is_shown:
        if index == key:
          return i
        index += 1
    return self.list[key]

  def __len__(self):
    #- list of shown items
    return len(filter(lambda n: n.is_shown, self.list))

  def __getitem__(self, key):
    return self.list[key]

  def __delitem__(self, i): del self.list[i]
  def __str__(self): return str(self.list)
