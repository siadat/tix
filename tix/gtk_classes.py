import gtk
import pango
from control import Control, UserMode, TixMode
from note import Note
from gtk_undobuffer import UndoableBuffer
import functools

class StatusBar(gtk.Statusbar):
  def __init__(self, *args):
    gtk.Statusbar.__init__(self, *args)
    self.statusbar_context = self.get_context_id("the status bar")
    self.set_has_resize_grip(False)

  def update(self, message):
    tix_mode = TixMode.OPTIONS[TixMode.current].upper()
    self.push(self.statusbar_context, "%s MODE %s" % (tix_mode, message))

class List(gtk.TreeView):
  def __init__(self, stored_items):
    types = [str] * 1
    note_items_model = gtk.ListStore(*types)
    all_modes = stored_items.modes()
    #checked_modes = set()
    todo_marker = "<span weight='bold' background='#709dbf' color='#fff'> ... </span> " #8a5

    for i, item in enumerate(stored_items):
      if not item.is_shown: continue

      item_modes = stored_items.sorted_item_modes(item)

      import utils
      modes = ""
      def f(sofar, m):
        regex = Control.get_last_regex()
        if regex and utils.search_regex(regex, m):
          return "%s<span background='#ee6' color='#000'> %s </span> " % (sofar, m)
        else:
          return "%s<span background='#d0ddef' color='#024'> %s </span> " % (sofar, m)
      modes = functools.reduce(f, item_modes, "")

      first_line = item.first_line

      if not first_line:
        first_line = "<span color='#999'>Empty</span>"
      else:
        first_line = "%s" % item.first_line
      
      if item.is_todo:
        note_items_model.append((
          '%s%s %s' % (modes, todo_marker, first_line, ),
        ))
      else:
        note_items_model.append((
          "%s %s" % (modes, first_line, ),
        ))
    gtk.TreeView.__init__(self, note_items_model)
    
    self.set_cursor(0)
    self.set_rules_hint(1)
    self.set_enable_search(False)
    self.set_headers_clickable(False)
    self.set_headers_visible(False)
    
    col1 = self.create_column(0, 'Notes')
    #col1 = self.create_column(0, 'Tags')
    #col2 = self.create_column(1, 'First line without tags')

    col1.set_max_width(200)
    #col2.set_max_width(300)

    self.append_column(col1)
    #self.append_column(col2)

    
    s = self.get_selection()
    s.set_mode(gtk.SELECTION_SINGLE)

    self.swindow = create_swindow()
    self.swindow.add(self)

  @staticmethod
  def create_column(id, name):
    r = gtk.CellRendererText()
    column = gtk.TreeViewColumn(name, r, markup=id)
    column.set_sort_column_id(id)
    #column.set_alignment(1)
    return column

class Editor(gtk.TextView):
  def __init__(self, *args):
    gtk.TextView.__init__(self, *args)
    self.set_editable(True)
    self.set_wrap_mode(gtk.WRAP_WORD)
    self.set_pixels_above_lines(2)
    self.set_pixels_inside_wrap(0)
    self.set_right_margin(2)
    self.set_left_margin(2)
    self.set_border_width(10)
    f = 64 * 1024 - 1
    color = (f,) * 3
    self.modify_bg(0, gtk.gdk.Color(*color))
    #color = map(lambda x: int(x), (f, f * 0.9, f * 0.5))

    #= dark background:
    #self.modify_bg(0, gtk.gdk.Color(10000,12000,0))
    #self.modify_base(0, gtk.gdk.Color(10000,12000,0))
    #self.modify_text(0, gtk.gdk.Color(*color))
    #=

    self.swindow = create_swindow()
    self.swindow.add(self)
    
    self.note = None
    
    self.texttagtable = gtk.TextTagTable()
    self.texttag_bold = gtk.TextTag("bold")
    self.texttag_bold.set_property("weight", pango.WEIGHT_BOLD)
    self.texttagtable.add(self.texttag_bold)

  def undo(self):
    self.get_buffer().undo()

  def redo(self):
    self.get_buffer().redo()

  def insert_date(self):
    import time
    import datetime

    buff = self.get_buffer()
    now = datetime.datetime.now()
    z = time.strftime("%Z")
    t = now.strftime("%Y-%m-%d-%H:%M:%S")
    buff.insert_at_cursor("%s-%s" % (t, z))

  def load_note(self, note=None):
    self.note = note
    buff = UndoableBuffer(self.texttagtable)
    if self.note:
      buff.set_text(note.load_fulltext_from_file())
    else:
      buff.set_text("")
    self.set_buffer(buff)
    if buff.undo_stack:
      buff.undo_stack.pop() # FIXME is it a safe way of removing the initial undo item (empty textbox)
    buff.place_cursor(buff.get_start_iter())

  def delete_current_file(self):
    dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL,
                               type=gtk.MESSAGE_QUESTION,
                               buttons=gtk.BUTTONS_YES_NO,
                               message_format="Are you sure you want to delete this file? \n%s" % self.note.fullpath())
    dialog.set_title("Delete file")
    response = dialog.run()
    dialog.destroy()
    if response == gtk.RESPONSE_YES:
      import os
      os.remove(self.note.fullpath())
      return True
    else:
      return False


  def save(self):
    buff = self.get_buffer()
    text = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
    if not self.note:
      import utils
      self.note = Note(utils.generate_filename(), utils.user_configurations['TIXPATH'], text)
    self.note.write_text_to_file(text)
    return self.note

  def mark_tags(self):
    #TODO
    pass

  def make_bold(self):
    import re
    buff = self.get_buffer()
    text = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
    for match in re.finditer(r'DONE', text, re.L | re.U):
      start = buff.get_iter_at_offset(match.start())
      end = buff.get_iter_at_offset(match.end())
      buff.apply_tag(self.texttag_bold, start, end)
    #if buff.get_selection_bounds() != ():
    #  start, end = buff.get_selection_bounds()
    #  print start, end
    #  buff.apply_tag(self.texttag_bold, start, end)

  #@staticmethod
  #def get_editor_text(editor):
  #  buff = editor.get_buffer()
  #  iter1 = buff.get_start_iter()
  #  iter2 = buff.get_end_iter()
  #  return buff.get_text(iter1, iter2)

def create_swindow():
  swindow = gtk.ScrolledWindow()
  swindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  swindow.set_shadow_type(gtk.SHADOW_IN)
  #swindow.set_border_width(10)
  return swindow
