import gtk
from control import Control, UserMode, TixMode
class List(gtk.TreeView):
  def __init__(self, stored_items):
    types = [str] * 2
    note_items_model = gtk.ListStore(*types)
    all_modes = stored_items.modes()
    for i, item in enumerate(stored_items):
      modes = " ".join([m for m in item.modes if m != all_modes[UserMode.current]])
      #bg_color = None # '#ddd' if item.is_todo else None
      if item.is_todo:
        note_items_model.append(("<b>%s</b>" % modes, "<b>%s</b>" % item.first_line))
      else:
        note_items_model.append((modes, "%s" % item.first_line))

    gtk.TreeView.__init__(self, note_items_model)
    
    self.set_cursor(0)
    self.set_rules_hint(True)
    self.set_enable_search(False)
    self.set_headers_clickable(False)
    self.set_headers_visible(False)
    
    self.append_column(self.create_column(0, 'Tags'))
    self.append_column(self.create_column(1, 'First Line'))
    
    s = self.get_selection()
    s.set_mode(gtk.SELECTION_SINGLE)

    self.swindow = create_swindow()
    self.swindow.add(self)

  @staticmethod
  def create_column(id, name):
    r = gtk.CellRendererText()
    column = gtk.TreeViewColumn(name, r, markup=id)
    column.set_sort_column_id(id)
    column.set_max_width(150)
    return column

class Editor(gtk.TextView):
  def __init__(self, *args):
    gtk.TextView.__init__(self, *args)
    self.set_editable(True)
    self.set_wrap_mode(gtk.WRAP_WORD)

    self.swindow = create_swindow()
    self.swindow.add(self)

  def undo(self):
    self.get_buffer().undo()

  def redo(self):
    self.get_buffer().redo()

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
  return swindow
