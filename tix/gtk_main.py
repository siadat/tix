#import pygtk
#pygtk.require('2.0')

import gtk
import sys
import utils
from note import Note, NoteList
from gtk_classes import List, Editor
from control import Control, UserMode, TixMode

class GtkMain:
  def create_editor(self):
    self.editor = Editor()
    self.editor.connect('key-press-event', self.keypress_reaction_editor)

    self.editor.set_pixels_above_lines(2)
    self.editor.set_pixels_inside_wrap(0)
    self.editor.set_right_margin(2)
    self.editor.set_left_margin(2)

    self.editor.set_border_width(10)
    f = 64 * 1024 - 1
    color = (f,) * 3
    self.editor.modify_bg(0, gtk.gdk.Color(*color))
    #color = map(lambda x: int(x), (f, f * 0.9, f * 0.5))
    #self.editor.modify_base(0, gtk.gdk.Color(10000,12000,0))
    #self.editor.modify_text(0, gtk.gdk.Color(*color))

  def create_list(self):
    self.tree_view = List(self.stored_items)
    self.tree_view.connect('row-activated', self.event_switch_to_edit_view)
    self.tree_view.connect('key-press-event', self.keypress_reaction_list)

  def create_statusbar(self):
    self.status_bar = gtk.Statusbar()
    self.statusbar_context = self.status_bar.get_context_id("the status bar")
    self.status_bar.push(self.statusbar_context, "TIX")
    self.status_bar.set_has_resize_grip(False)
    self.vbox.pack_end(self.status_bar, False, False, 0)
    self.status_bar.show()

  def create_window(self):
    self.main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.main_window.set_title("Tix")
    self.main_window.set_default_size(int(500 * 1.4), int(400 * 1.4))
    self.main_window.connect("delete-event", self.delete_event)
    self.main_window.connect("destroy", self.event_destroy, None)
    self.main_window.set_border_width(10)
    
    self.vbox = gtk.VBox(False, 1)
    self.main_window.add(self.vbox)
    
  #def create_toolbar(self):
  #  toolbar = gtk.Toolbar()
  #  toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
  #  toolbar.set_tooltips(False)
  #  toolbar.append_item("save", "save tooltip", "shhh... this is a private tooltip", None, self.event_undo, None)
  #  toolbar.append_item("cancel", "cancel tooltip", "shhh... this is a private tooltip", None, self.event_redo, None)
  #  return toolbar

  # {{{ Events
  def event_select_prev(self, widget, event, data=None):
    if TixMode.current == TixMode.LIST:
      path, col = self.tree_view.get_cursor()
      if path:
        new_index = path[0] - 1
        if new_index >= 0:
          self.tree_view.set_cursor(new_index)

  def event_select_next(self, widget, event, data=None):
    if TixMode.current == TixMode.LIST:
      path, col = self.tree_view.get_cursor()
      if path:
        new_index = path[0] + 1
        if new_index < len(self.tree_view.get_model()):
          self.tree_view.set_cursor(new_index)

  def event_prev_tag_mode(self, widget, event, data=None): pass # TODO
  def event_next_tag_mode(self, widget, event, data=None): pass # TODO

  def event_select_first(self, widget, event, data=None):
    if TixMode.current == TixMode.LIST:
      self.tree_view.set_cursor(0)

  def event_select_last(self, widget, event, data=None):
    if TixMode.current == TixMode.LIST:
      s = len(self.tree_view.get_model())
      if s > 0:
        self.tree_view.set_cursor(s - 1)

  def event_select_last_visible(self, widget, event, data=None):
    if TixMode.current == TixMode.LIST:
      path_start, path_end = self.tree_view.get_visible_range()
      if path_end:
        new_index = path_end[0]
        self.tree_view.set_cursor(new_index)

  def event_select_first_visible(self, widget, event, data=None):
    if TixMode.current == TixMode.LIST:
      path_start, path_end = self.tree_view.get_visible_range()
      if path_start:
        new_index = path_start[0]
        self.tree_view.set_cursor(new_index)

  def event_select_middle_visible(self, widget, event, data=None):
    if TixMode.current == TixMode.LIST:
      path_start, path_end = self.tree_view.get_visible_range()
      if path_start and path_end:
        new_index = (path_start[0] + path_end[0]) / 2
        self.tree_view.set_cursor(new_index)

  def event_add_new_note(self, widget, event, data=None):
    if TixMode.current == TixMode.LIST:
      TixMode.current = TixMode.EDIT

      path, col = self.tree_view.get_cursor()
      current_visible_index = path[0]

      self.editor.load_note(None)
      self.status_bar.push(self.statusbar_context, 'MODE: EDIT (new file)')

      self.vbox.remove(self.tree_view.get_parent())
      self.vbox.add(self.editor.get_parent())
      self.editor.grab_focus()
      self.main_window.show_all()

  def event_toggle_view(self, widget, event, data=None):
    nbr_modes = len(TixMode.OPTIONS)
    reverse = False
    addition = 1 if not reverse else -1
    TixMode.current = (TixMode.current + addition) % nbr_modes

    if TixMode.current == TixMode.TAGS:
      TixMode.current = (TixMode.current + addition) % nbr_modes

    if TixMode.current == TixMode.EDIT:
      self.event_switch_to_edit_view(None, None)
    elif TixMode.current == TixMode.LIST:
      self.event_switch_to_list_view(None, None)

  def event_switch_to_edit_view(self, widget, event, data=None):
    TixMode.current = TixMode.EDIT

    path, col = self.tree_view.get_cursor()
    current_visible_index = path[0]

    self.editor.load_note(self.stored_items[current_visible_index])
    self.status_bar.push(self.statusbar_context, 'MODE: EDIT "%s"' % self.stored_items[current_visible_index].fullpath())

    self.vbox.remove(self.tree_view.get_parent())
    self.vbox.add(self.editor.get_parent())
    self.editor.grab_focus()
    self.main_window.show_all()

  def event_switch_to_list_view(self, widget, event, data=None):
    TixMode.current = TixMode.LIST
    self.status_bar.push(self.statusbar_context, "MODE: LIST")
    if Control.reload_notes:
      self.stored_items.load(self.notes_root, self.recursive)
      self.create_list()
      Control.reload_notes = False
    self.vbox.remove(self.editor.get_parent())
    self.vbox.add(self.tree_view.get_parent())
    self.tree_view.grab_focus()
    self.main_window.show_all()
    

  def event_destroy(self, widget, event, data=None):
    if TixMode.current == TixMode.LIST:
      gtk.main_quit()
    else:
      self.event_switch_to_list_view(None, None)

  def delete_event(self, widget, event, data=None):
    if TixMode.current == TixMode.LIST:
      gtk.main_quit()
      return False
    else:
      self.event_switch_to_list_view(None, None)
      return True

  def event_insert_date(self, widget, event, data=None):
    if TixMode.current == TixMode.EDIT:
      if event.state == gtk.gdk.CONTROL_MASK:
        self.editor.insert_date()

  def event_save(self, widget, event, data=None):
    if TixMode.current == TixMode.EDIT:
      if event.state == gtk.gdk.CONTROL_MASK:
        Control.reload_notes = True
        n = self.editor.save()
        self.status_bar.push(self.statusbar_context, 'MODE: EDIT "%s"' % n.fullpath())

  #def event_bold(self, widget, event, data=None):
  #  if TixMode.current == TixMode.EDIT:
  #    if event.state == gtk.gdk.CONTROL_MASK:
  #      self.editor.make_bold()

  def event_undo(self, widget, event, data=None):
    if TixMode.current == TixMode.EDIT:
      if event.state == gtk.gdk.CONTROL_MASK:
        self.editor.undo()

  def event_redo(self, widget, event, data=None):
    if TixMode.current == TixMode.EDIT:
      if event.state == gtk.gdk.CONTROL_MASK:
        self.editor.redo()
  # }}}

  def keypress_reaction_list(self, widget, event, data=None):
    try:
      f = self.event_dict_list[event.keyval]
      f(widget, event, data)
    except KeyError:
      pass

  def keypress_reaction_editor(self, widget, event, data=None):
    try:
      f = self.event_dict_editor[event.keyval]
      f(widget, event, data)
    except KeyError:
      pass

  def __init__(self):
    utils.get_user_config()
    self.stored_items = NoteList()

    self.event_dict_list = dict({
      gtk.keysyms.Tab: self.event_toggle_view,
      #gtk.keysyms.Escape: self.event_toggle_view,
      gtk.keysyms.a: self.event_add_new_note,
      gtk.keysyms.q:   self.event_destroy,
      gtk.keysyms.j:   self.event_select_next,
      gtk.keysyms.k:   self.event_select_prev,
      gtk.keysyms.G:   self.event_select_last,
      gtk.keysyms.M:   self.event_select_middle_visible,
      gtk.keysyms.L:   self.event_select_last_visible,
      gtk.keysyms.H:   self.event_select_first_visible,
      gtk.keysyms.g:   self.event_select_first,
      gtk.keysyms.n:   self.event_next_tag_mode,
      gtk.keysyms.p:   self.event_prev_tag_mode,
    })

    self.event_dict_editor = dict({
      gtk.keysyms.Escape:   self.event_destroy,
      gtk.keysyms.z:   self.event_undo,
      gtk.keysyms.r:   self.event_redo,
      gtk.keysyms.s:   self.event_save,
      gtk.keysyms.d:   self.event_insert_date,
      #gtk.keysyms.b:   self.event_bold,
    })

  def main(self, notes_root, recursive):
    self.notes_root = notes_root
    self.recursive = recursive
    self.stored_items.load(self.notes_root, self.recursive)

    Control.reload_notes = True
    self.is_searching = False

    self.create_window()
    self.create_list()
    self.create_editor()
    self.create_statusbar()
    
    self.event_switch_to_list_view(None, None, None)

    gtk.main()

if __name__ == "__main__":
  hello = GtkMain()
  sys.exit(hello.main())
