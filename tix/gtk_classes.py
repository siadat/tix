import gtk
import pango
from control import Control, UserMode, TixMode
from gtk_undobuffer import UndoableBuffer
class List(gtk.TreeView):
  def __init__(self, stored_items):
    types = [str] * 2
    note_items_model = gtk.ListStore(*types)
    all_modes = stored_items.modes()
    for i, item in enumerate(stored_items):
      modes = " ".join(["<span background='#eee' color='#000'> %s </span>" % m.upper() for m in item.modes if m != all_modes[UserMode.current]])
      first_line = item.first_line
      #bg_color = None # '#ddd' if item.is_todo else None
      if not modes: modes = "<span color='#999'>None</span>"
      if not first_line: first_line = "<span color='#999'>Empty</span>"

      todo_marker = '<span size="smaller" color="#579" weight="bold" background="#d0ddef"> TODO </span> ' #8a5
      if item.is_todo:
        note_items_model.append((
          '%s%s' % (todo_marker, modes),
          '%s%s' % ('', first_line),
        ))
      else:
        note_items_model.append((
          modes, 
          first_line,
        ))

    gtk.TreeView.__init__(self, note_items_model)
    
    self.set_cursor(0)
    self.set_rules_hint(False)
    self.set_enable_search(False)
    self.set_headers_clickable(False)
    self.set_headers_visible(True)
    
    col1 = self.create_column(0, 'Tags')
    col2 = self.create_column(1, 'First line without tags')
    col1.set_max_width(200)
    col2.set_max_width(400)

    self.append_column(col1)
    self.append_column(col2)

    
    s = self.get_selection()
    s.set_mode(gtk.SELECTION_SINGLE)

    self.swindow = create_swindow()
    self.swindow.add(self)

  @staticmethod
  def create_column(id, name):
    r = gtk.CellRendererText()
    column = gtk.TreeViewColumn(name, r, markup=id)
    column.set_sort_column_id(id)
    return column

class Editor(gtk.TextView):
  def __init__(self, *args):
    gtk.TextView.__init__(self, *args)
    self.set_editable(True)
    self.set_wrap_mode(gtk.WRAP_WORD)
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

  def load_note(self, note):
    self.note = note
    buff = UndoableBuffer(self.texttagtable)
    buff.set_text(note.load_fulltext_from_file())
    self.set_buffer(buff)
    buff.undo_stack.pop() # FIXME is it a safe way of removing the initial undo item (empty textbox)

  def save(self):
    buff = self.get_buffer()
    text = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
    self.note.write_text_to_file(text)
    #if len(buff.undo_stack) > 0:
    #  return True # Changed
    #else:
    #  return False # Unchanged

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
