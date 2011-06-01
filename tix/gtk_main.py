#import pygtk
#pygtk.require('2.0')

import gtk
import pango

import sys
import utils
from note import Note, NoteList
from gtk_classes import List, Editor, StatusBar
from control import Control, UserMode, TixMode

class GtkMain:
  def create_commandline(self):
    self.commandline = gtk.Entry(1024)
    self.commandline.connect('changed', self.keypress_reaction_commandline_changed)
    self.commandline.connect('key-press-event', self.keypress_reaction_commandline_keypressed)
    self.commandline.connect('focus-out-event', self.commandline_focus_out_event)
    self.commandline.set_editable(1)
    font_desc = pango.FontDescription('monospace')
    self.commandline.modify_font(font_desc)
    #self.commandline.set_has_frame(False)
    #self.commandline.set_activates_default(True)

  def create_editor(self):
    self.editor = Editor()
    self.editor.connect('key-press-event', self.keypress_reaction_editor)

  def create_list(self):
    self.tree_view = List(self.stored_items)
    self.tree_view.connect('row-activated', self.event_switch_to_edit_view)
    self.tree_view.connect('key-press-event', self.keypress_reaction_list)

  def create_statusbar(self):
    self.status_bar = StatusBar()
    self.status_bar.update("TIX")
    self.vbox.pack_end(self.status_bar, False, False, 0)
    self.status_bar.show()

  def create_window(self):
    self.main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.main_window.set_title("Tix")
    self.main_window.set_default_size(int(500 * 1.1), int(400 * 1.1))
    self.main_window.set_border_width(10)
    #self.main_window.fullscreen()
    self.main_window.connect("delete-event", self.delete_event)
    self.main_window.connect("destroy", self.event_destroy, None)
    
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
  def commandline_focus_out_event(self, widget, event, data=None):
    self.commandline.set_text("")

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

  def event_reload_config(self, widget, event, data=None):
    utils.get_user_config()

    self.vbox.remove(self.tree_view.get_parent())
    self.create_list()
    Control.reload_notes = True
    self.event_switch_to_list_view(None, None)

  def event_edit_config(self, widget, event, data=None):
    curr_note = Note('tix.cfg', utils.user_configurations['TIXPATH'], None)
    self.show_note_in_edit_mode(curr_note)

  def show_note_in_edit_mode(self, curr_note):
    TixMode.current = TixMode.EDIT
    self.editor.load_note(curr_note)
    self.status_bar.update('"%s"' % curr_note.fullpath())
    self.vbox.remove(self.tree_view.get_parent())
    self.vbox.add(self.editor.get_parent())
    self.editor.grab_focus()
    self.main_window.show_all()

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

      #path, col = self.tree_view.get_cursor()
      #current_visible_index = path[0]

      self.editor.load_note(None)
      self.status_bar.update('(new file)')

      self.vbox.remove(self.tree_view.get_parent())
      self.vbox.add(self.editor.get_parent())
      self.editor.grab_focus()
      self.main_window.show_all()
  
  def event_execute_command(self, widget, event, data=None):
    regex = self.commandline.get_text()
    if len(regex) > 0:
      # Notice we're not striping '#'
      if regex[0] in ('/', '?'): regex = regex[1:]
    #if regex.strip(): 
    Control.regex_patterns.append(regex)
    utils.append_line_to_history("/" + regex)
    Control.current_regex_index = len(Control.regex_patterns)
    nbr_visible = self.stored_items.filter()
    if nbr_visible == 1:
      curr_note = self.stored_items.get_visible(0)
      self.show_note_in_edit_mode(curr_note)
    else:
      # repopulate tree_view:
      self.vbox.remove(self.tree_view.get_parent())
      self.create_list()

      Control.reload_notes = False
      self.event_switch_to_list_view(None, None)

      self.tree_view.grab_focus()

  def event_check_commandline_text(self, widget, data=None):
    if self.commandline.get_text_length() == 0:
      self.event_focus_list(None, None)

  def event_commandline_home(self, widget, event, data=None):
    l = self.commandline.get_text_length()
    if l > 0:
      self.commandline.set_position(1)
      widget.emit_stop_by_name("key-press-event")

  def event_next_search_regex(self, widget, event, data=None):
    # FIXME focus is grabbed by tree_view
    if Control.current_regex_index < len(Control.regex_patterns) - 1:
      Control.current_regex_index += 1
      self.commandline.set_text("/%s" % Control.regex_patterns[Control.current_regex_index])
      l = self.commandline.get_text_length()
      self.commandline.set_position(l)
    elif Control.current_regex_index == len(Control.regex_patterns) - 1:
      Control.current_regex_index += 1
      self.commandline.set_text("/")
      l = self.commandline.get_text_length()
      self.commandline.set_position(l)

    return True
    #widget.emit_stop_by_name("key-press-event")

  def event_prev_search_regex(self, widget, event, data=None):
    # FIXME focus is grabbed by tree_view
    widget.emit_stop_by_name("key-press-event")
    if Control.current_regex_index > 0:
      Control.current_regex_index -= 1
      self.commandline.set_text("/%s" % Control.regex_patterns[Control.current_regex_index])
      l = self.commandline.get_text_length()
      self.commandline.set_position(l)
    return True
    #self.commandline.emit_stop_by_name("key-press-event")
    #widget.stop_emission("key-press-event")

  def event_reset_search(self, widget, event, data=None):
    Control.regex_patterns.append("")

    # see also: event_execute_command
    self.stored_items.filter()
    # repopulate tree_view:
    self.vbox.remove(self.tree_view.get_parent())
    self.create_list()

    Control.reload_notes = False
    self.event_switch_to_list_view(None, None)

    self.commandline.set_text("")
    self.tree_view.grab_focus()

  def event_focus_list(self, widget, event, data=None):
    self.tree_view.grab_focus()

  def event_focus_commandline_search_mode(self, widget, event, data=None):
    if event.keyval == gtk.keysyms.numbersign \
    or event.keyval == gtk.keysyms.slash \
    or (event.keyval == gtk.keysyms.f and event.state == gtk.gdk.CONTROL_MASK):
      if event.keyval == gtk.keysyms.numbersign:
        self.commandline.set_text('/#')
      else:
        self.commandline.set_text('/')
      self.commandline.grab_focus()
      l = self.commandline.get_text_length()
      self.commandline.set_position(l)

  def event_focus_commandline_command_mode(self, widget, event, data=None):
    self.commandline.set_text(':')

    self.commandline.grab_focus()
    l = self.commandline.get_text_length()
    self.commandline.set_position(l)

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
    path, col = self.tree_view.get_cursor()
    if path:
      current_visible_index = path[0]
      curr_note = self.stored_items.get_visible(current_visible_index)

      self.show_note_in_edit_mode(curr_note)

  def event_switch_to_list_view(self, widget, event, data=None):
    TixMode.current = TixMode.LIST
    self.status_bar.update("- Search: %s" % Control.get_last_regex() if Control.get_last_regex() else "")
    if Control.reload_notes:
      self.stored_items.load(self.notes_root, self.recursive)
      self.create_list()
      Control.reload_notes = False
    self.vbox.remove(self.editor.get_parent())
    self.vbox.pack_start(self.commandline, False, False, 0)
    self.vbox.add(self.tree_view.get_parent())
    self.tree_view.grab_focus()
    self.main_window.show_all()

  def event_delete_note(self, widget, event, data=None):
    if event.state == 0: # no gtk.gdk.CONTROL_MASK or MOD1_MASK
      if self.editor.delete_current_file():
        Control.reload_notes = True
        self.event_switch_to_list_view(None, None)

  def event_destroy(self, widget, event, data=None):
    gtk.main_quit()
    #if TixMode.current == TixMode.LIST:
    #  gtk.main_quit()
    #else:
    #  self.event_switch_to_list_view(None, None)

  def delete_event(self, widget, event, data=None):
    gtk.main_quit()
    return False
    #if TixMode.current == TixMode.LIST:
    #  gtk.main_quit()
    #  return False
    #else:
    #  self.event_switch_to_list_view(None, None)
    #  return True

  def event_insert_date(self, widget, event, data=None):
    if TixMode.current == TixMode.EDIT:
      if event.state == gtk.gdk.CONTROL_MASK:
        self.editor.insert_date()

  def event_save(self, widget, event, data=None):
    if TixMode.current == TixMode.EDIT:
      if event.state == gtk.gdk.CONTROL_MASK:
        Control.reload_notes = True
        n = self.editor.save()
        self.status_bar.update('"%s"' % n.fullpath())

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

  def keypress_reaction_commandline_changed(self, widget, data=None):
    self.event_check_commandline_text(widget, data)

  def keypress_reaction_commandline_keypressed(self, widget, event=None, data=None):
    #if self.commandline.get_position() < 1:
    #  l = self.commandline.get_text_length()
    #  if l > 0:
    #    self.commandline.set_position(1)
    try:
      f = self.event_dict_commandline[event.keyval]
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
    Control.regex_patterns = utils.load_search_history()
    self.stored_items = NoteList()

    self.event_dict_commandline = dict({
      gtk.keysyms.Escape: self.event_focus_list,
      gtk.keysyms.Return: self.event_execute_command,
      gtk.keysyms.Up: self.event_prev_search_regex,
      gtk.keysyms.Down: self.event_next_search_regex,
      gtk.keysyms.Home: self.event_commandline_home,
    })

    self.event_dict_list = dict({
      # List to commandline
      #gtk.keysyms.colon: self.event_focus_commandline_command_mode,
      gtk.keysyms.slash: self.event_focus_commandline_search_mode,
      gtk.keysyms.f: self.event_focus_commandline_search_mode,
      gtk.keysyms.numbersign: self.event_focus_commandline_search_mode,

      # List to editor
      gtk.keysyms.Escape: self.event_reset_search,
      #gtk.keysyms.Tab: self.event_toggle_view,
      gtk.keysyms.a: self.event_add_new_note,

      # List
      #gtk.keysyms.q: self.event_destroy,
      gtk.keysyms.j: self.event_select_next,
      gtk.keysyms.k: self.event_select_prev,
      gtk.keysyms.G: self.event_select_last,
      gtk.keysyms.M: self.event_select_middle_visible,
      gtk.keysyms.L: self.event_select_last_visible,
      gtk.keysyms.H: self.event_select_first_visible,
      gtk.keysyms.g: self.event_select_first,
      gtk.keysyms.n: self.event_next_tag_mode,
      gtk.keysyms.p: self.event_prev_tag_mode,
      gtk.keysyms.F3: self.event_edit_config,
      gtk.keysyms.F5: self.event_reload_config,
    })

    self.event_dict_editor = dict({
      gtk.keysyms.Escape: self.event_switch_to_list_view,
      gtk.keysyms.z: self.event_undo,
      gtk.keysyms.r: self.event_redo,
      gtk.keysyms.s: self.event_save,
      gtk.keysyms.d: self.event_insert_date,
      gtk.keysyms.F4: self.event_delete_note,
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
    self.create_commandline()
    
    self.event_switch_to_list_view(None, None, None)

    gtk.main()

if __name__ == "__main__":
  hello = GtkMain()
  sys.exit(hello.main())
