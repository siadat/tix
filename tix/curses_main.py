# Copyright (c) 2011 Sina Siadatnejad 
# License: MIT License
# vim: encoding=utf-8 sw=2 ts=2 sts=2 ai et
import re
import os
import sys
import copy
import utils
import random
import curses
import curses.textpad
import threading

from curses_view import CursesView
from control import Control,TixMode, UserMode
from note import NoteList

curses_view = CursesView()

class CursesRunner(object):

  class Loader(threading.Thread):

    def __init__(self, outer):
      threading.Thread.__init__(self)
      self.outer = outer

    def run(self):
      Control.reload_thread_lock.acquire()
      self.outer.stored_items = utils.load(self.outer.notes_root, self.outer.recursive)
      self.outer.stored_items.sort_by_modification_date()
      nbr_objects = len(self.outer.stored_items)

      list_modes = self.outer.stored_items.modes()
      current_mode = list_modes[UserMode.current_user_mode]
      
      for i, note in enumerate(self.outer.stored_items):
        note.process_meta(i)

        if (current_mode == UserMode.ALL or current_mode in note.modes) and note.is_search_match(Control.get_last_regex()):
          note.visible(True)
        else:
          note.visible(False)

        if i % 10 == 0 or i >= nbr_objects - 1:
          curses_view.complete_redraw(self.outer.stored_items)
      if len(self.outer.stored_items) == 0:
        curses_view.complete_redraw(self.outer.stored_items)

      Control.reload_thread_lock.release()

  @classmethod
  def run(self, notes_root, recursive): #def run(self, stdscr, notes_root, recursive):

    utils.get_user_config()

    # for debugging:
    #curses_view.end_curses()
    #utils.get_user_config()
    #note_obj_list = utils.load(notes_root, recursive)
    #exit()

    if not os.path.exists(notes_root):
      curses_view.end_curses()
      print('No such directory "%s"' % notes_root)
      exit()

    self.stored_items = NoteList()
    self.recursive = recursive
    self.notes_root = notes_root

    Control.reload_notes = True
    self.is_searching = False

    # {{{ funcs for key events
    def keypress_list_pageup():
      Control.reload_notes = False
      curses_view.list_scroll_top -= curses_view.get_list_capacity()
      Control.list_visible_index -= curses_view.get_list_capacity()

    def keypress_list_pagedown():
      Control.reload_notes = False
      curses_view.list_scroll_top += curses_view.get_list_capacity()
      Control.list_visible_index += curses_view.get_list_capacity()

    def keypress_select_first_in_view():
      Control.reload_notes = False
      if TixMode.current_tix_mode == TixMode.LIST_TIX_MODE:
        i = Control.list_visible_index
        Control.list_visible_index = curses_view.list_scroll_top
        if i != Control.list_visible_index:
          curses_view.note_scroll_top = 0
          Control.list_visible_index = curses_view.adjust_scroll(len(self.stored_items), Control.list_visible_index)

    def keypress_select_last_in_view():
      Control.reload_notes = False
      if TixMode.current_tix_mode == TixMode.LIST_TIX_MODE:
        i = Control.list_visible_index
        Control.list_visible_index = curses_view.list_scroll_top + curses_view.get_list_capacity() - 1
        if i != Control.list_visible_index:
          curses_view.note_scroll_top = 0
          Control.list_visible_index = curses_view.adjust_scroll(len(self.stored_items), Control.list_visible_index)

    def keypress_select_middle_in_view():
      Control.reload_notes = False
      if TixMode.current_tix_mode == TixMode.LIST_TIX_MODE:
        i = Control.list_visible_index

        max_nbr_items_in_screen = curses_view.get_list_capacity() - 1
        if max_nbr_items_in_screen > len(self.stored_items):
          Control.list_visible_index = curses_view.list_scroll_top + (len(self.stored_items) - (curses_view.margin_top + curses_view.margin_bottom)) / 2
        else:
          Control.list_visible_index = curses_view.list_scroll_top + max_nbr_items_in_screen / 2

        if i != Control.list_visible_index:
          curses_view.note_scroll_top = 0
          Control.list_visible_index = curses_view.adjust_scroll(len(self.stored_items), Control.list_visible_index)

    def keypress_select_next():
      Control.reload_notes = False
      if TixMode.current_tix_mode == TixMode.NOTE_TIX_MODE:
        pass
      elif TixMode.current_tix_mode == TixMode.LIST_TIX_MODE:
        curses_view.note_scroll_top = 0
        Control.list_visible_index += 1
        Control.list_visible_index = curses_view.adjust_scroll(len(self.stored_items), Control.list_visible_index)

    def keypress_select_prev():
      Control.reload_notes = False
      if TixMode.current_tix_mode == TixMode.NOTE_TIX_MODE:
        pass
      elif TixMode.current_tix_mode == TixMode.LIST_TIX_MODE:
        curses_view.note_scroll_top = 0
        Control.list_visible_index -= 1
        Control.list_visible_index = curses_view.adjust_scroll(len(self.stored_items), Control.list_visible_index)

    def keypress_select_last():
      Control.reload_notes = False
      if TixMode.current_tix_mode == TixMode.NOTE_TIX_MODE:
        pass # TODO curses_view.note_scroll_top = 0
      elif TixMode.current_tix_mode == TixMode.LIST_TIX_MODE:
        curses_view.note_scroll_top = 0
        Control.list_visible_index = len(self.stored_items) - 1
        Control.list_visible_index = curses_view.adjust_scroll(len(self.stored_items), Control.list_visible_index)

    def keypress_select_first():
      Control.reload_notes = False
      if TixMode.current_tix_mode == TixMode.NOTE_TIX_MODE:
        curses_view.note_scroll_top = 0
      elif TixMode.current_tix_mode == TixMode.LIST_TIX_MODE:
        curses_view.note_scroll_top = 0
        Control.list_visible_index = 0
        curses_view.list_scroll_top = 0

    def keypress_change_sorting_order():
      Control.current_sortby = (Control.current_sortby + 1) % len(Control.SORTBYS)
      if Control.current_sortby == Control.SORTBY_SHUF:
        Control.current_sortby = (Control.current_sortby + 1) % len(Control.SORTBYS)

      Control.reload_notes = False
      item_id = self.stored_items.get_visible(Control.list_visible_index).id

      if Control.current_sortby == Control.SORTBY_DATE:
        self.stored_items.sort_by_modification_date()
      elif Control.current_sortby == Control.SORTBY_FILENAME:
        self.stored_items.sort_by_filename()

      new_index = 0
      for i, item in enumerate(self.stored_items):
        if item.id == item_id:
          new_index = i
          break

      curses_view.note_scroll_top = 0
      Control.list_visible_index = new_index

    def keypress_shuf_order():
      Control.reload_notes = False
      Control.current_sortby = Control.SORTBY_SHUF
      item_id = self.stored_items.get_visible(Control.list_visible_index).id
      random.shuffle(self.stored_items)
      new_index = 0
      for i, item in enumerate(self.stored_items):
        if item.id == item_id:
          new_index = i
          break

      curses_view.note_scroll_top = 0
      Control.list_visible_index = new_index

    def keypress_insert_as_first():
      Control.reload_notes = False
      curses.endwin()
      n = utils.new_note()
      if n:
        curses_view.note_scroll_top = 0
        Control.list_visible_index = 0
        Control.list_visible_index = curses_view.adjust_scroll(len(self.stored_items), Control.list_visible_index)
        Control.reload_notes = True

    def keypress_toggle_filename_view():
      Control.reload_notes = False
      if TixMode.current_tix_mode == TixMode.LIST_TIX_MODE:
        Control.list_view_mode += 1
        Control.list_view_mode = Control.list_view_mode % len(Control.LIST_VIEWS)

    def keypress_cycle_modes_reverse():
      keypress_cycle_modes(True)

    def keypress_cycle_modes(reverse=False):
      Control.reload_notes = False
      list_modes = self.stored_items.modes()
      nbr_modes = len(list_modes)

      if nbr_modes == 0: return

      addition = 1 if not reverse else -1
      UserMode.current_user_mode = (UserMode.current_user_mode + addition) % nbr_modes
      
      for note in self.stored_items:
        if list_modes[UserMode.current_user_mode] == UserMode.ALL or list_modes[UserMode.current_user_mode] in note.modes:
          note.visible(True)
        else:
          note.visible(False)

    def keypress_read():
      Control.reload_notes = False
      curses.endwin()
      filename = self.stored_items.get_visible(Control.list_visible_index).fullpath()
      utils.open_file_in_reader(filename)

    def keypress_edit():
      Control.reload_notes = True
      curses.endwin()
      old_note = self.stored_items.get_visible(Control.list_visible_index)
      edited_note = utils.edit_note(old_note)
      curses_view.note_scroll_top = 0
      Control.list_visible_index = 0

    def keypress_switch_to_list_mode():
      Control.reload_notes = False
      TixMode.current_tix_mode = TixMode.LIST_TIX_MODE

    def keypress_switch_to_note_mode():
      Control.reload_notes = False
      TixMode.current_tix_mode = TixMode.NOTE_TIX_MODE

    def pressed_slash():
      Control.reload_notes = False
      Control.reload_thread_lock.acquire()

      def validator(c):
        if c == 10:
          return 7 # RETURN key -- CTRL-g = 7 and CTRL-j = 10
        else:
          curses_view.search_textbox.do_command(c)

          if c == curses.KEY_UP and Control.current_regex_index > 0:
            Control.current_regex_index -= 1
            curses_view.footer_pad.clear()
            CursesView.add_str(curses_view.footer_pad, curses_view.search_prompt + Control.regex_patterns[Control.current_regex_index])
          elif c == curses.KEY_DOWN and Control.current_regex_index < len(Control.regex_patterns) - 1:
            Control.current_regex_index += 1
            curses_view.footer_pad.clear()
            CursesView.add_str(curses_view.footer_pad, curses_view.search_prompt + Control.regex_patterns[Control.current_regex_index])
          elif c == curses.KEY_DOWN and Control.current_regex_index == len(Control.regex_patterns) - 1:
            Control.current_regex_index += 1
            curses_view.footer_pad.clear()
            CursesView.add_str(curses_view.footer_pad, curses_view.search_prompt)

          if curses_view.search_textbox.gather() is '':
            return 7

      regex = ""
      curses.curs_set(1)
      Control.current_regex_index = len(Control.regex_patterns)
      curses_view.footer_pad.clear()
      CursesView.add_str(curses_view.footer_pad, curses_view.search_prompt)
      self.is_searching = True
      regex = curses_view.search_textbox.edit(validator)
      self.is_searching = False
      regex = regex[len(curses_view.search_prompt):]
      if regex.strip(): Control.regex_patterns.append(regex)
      curses.curs_set(0)
      Control.list_visible_index = 0
      Control.list_visible_index = curses_view.adjust_scroll(len(self.stored_items), Control.list_visible_index)

      list_modes = self.stored_items.modes()
      current_mode = list_modes[UserMode.current_user_mode]
      for note in self.stored_items:
        if (current_mode == UserMode.ALL or current_mode in note.modes) and note.is_search_match(regex):
          note.visible(True)
        else:
          note.visible(False)

      Control.reload_thread_lock.release()

    key_to_action = dict({
      ord('M'): keypress_select_middle_in_view,
      ord('H'): keypress_select_first_in_view,
      ord('L'): keypress_select_last_in_view,
      ord('j'): keypress_select_next,
      ord('k'): keypress_select_prev,
      ord('h'): keypress_switch_to_list_mode,
      ord('l'): keypress_switch_to_note_mode,
      ord('g'): keypress_select_first,
      ord('G'): keypress_select_last,
      ord('a'): keypress_insert_as_first,
      ord('r'): keypress_read,
      ord('\t'): keypress_cycle_modes,
      9: keypress_cycle_modes,
      353: keypress_cycle_modes_reverse,
      ord('f'): keypress_toggle_filename_view,
      ord('s'): keypress_change_sorting_order,
      ord('S'): keypress_shuf_order,
      ord('/'): pressed_slash,
      10: keypress_edit,
      curses.KEY_ENTER: keypress_edit,
      curses.KEY_DOWN: keypress_select_next,
      curses.KEY_UP: keypress_select_prev,
      curses.KEY_HOME: keypress_select_first,
      curses.KEY_END: keypress_select_last,
      curses.KEY_NPAGE: keypress_list_pagedown,
      curses.KEY_PPAGE: keypress_list_pageup,
      curses.KEY_LEFT: keypress_switch_to_list_mode,
      curses.KEY_RIGHT: keypress_switch_to_note_mode,
    })
    #}}}

    while True:
      curses_view.update_screen_size()
      curses_view.recalculate_note_width()
      curses_view.create_footer_pad()
      curses_view.create_note_pad()

      if Control.reload_notes:
        if not Control.reload_thread_lock.locked():
          t = self.Loader(self)
          t.start()
      elif not Control.reload_thread_lock.locked():
        curses_view.complete_redraw(self.stored_items)

      Control.reload_notes = False

      if len(self.stored_items) == 0:
        # TODO this is temporary workround, problem = first arrow key hit does nothing
        c = curses_view.keyboard_pad.getch()
      else:
        c = curses_view.screen.getch()

      utils.log(c)

      if c == ord('q'): break
      f = key_to_action.get(c)
      if f: f()

    curses_view.end_curses()
