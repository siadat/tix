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
    self.is_processed = False

  def fullpath(self):
    return os.path.join(self.path, self.filename)

  def is_a_match(self, regex, flags = 0):
    try:
      if regex.strip() is '': return True
      regex = regex.replace('#', '\\#')
      return re.search(regex, self.text, # self.path + self.filename + self.text,
          re.MULTILINE | re.DOTALL | re.VERBOSE | flags)
    except re.error:
      return True

  def process_meta(self, id):
    self.id = id
    self.is_todo = self.is_a_match(r'\b(TODO|DEADLINE)\b[^\'"`]')
    self.is_someday = self.is_a_match(r'\b(SOMEDAY)\b[^\'"`]')
    self.first_line = utils.get_first_line(self.text)
    self.is_processed = True
    self.text = " ".join(set([w.lower() for w in self.text.replace(r'\n',' ').split(' ')])) # self.text[:200] # FIXME
    #self.nbr_of_lines = utils.get_number_of_lines(self.text, 80)

  def is_search_match(self, regex):
    return self.is_a_match(regex, re.IGNORECASE)

  def visible(self, visibility):
    self.is_shown = visibility

  def load_text(self):
    with open(self.fullpath(), 'r') as f:
      return f.read()




class NoteList(collections.MutableSequence):
  """Holds all loaded notes."""
  def __init__(self):
    self.list = list()
    self.oktype = Note
    self._modes_set = set([UserMode.ALL, UserMode.NOTAG])

  def reset(self):
    del self.list[:]

  def check(self, v):
    if not isinstance(v, self.oktype):
      raise TypeError, v

  def group_todo(self):
    todo_list = [n for n in self.list if n.is_todo]
    self.list = [n for n in self.list if not n.is_todo]
    self.list = todo_list + self.list

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

  def insert(self, i, v):
    self.check(v)
    self._modes_set = self._modes_set.union(v.modes)
    self.list.insert(i, v)

  def modes(self):
    def comp(a, b):
      v1 = a.lower().replace(utils.TAG_STARTS_WITH, 'z')
      v2 = b.lower().replace(utils.TAG_STARTS_WITH, 'z')
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
