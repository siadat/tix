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
from control import Control, TixMode, UserMode, SortMode
from note import NoteList

curses_view = CursesView()

class CursesMain(object):
  class Loader(threading.Thread):
    def __init__(self, outer):
      threading.Thread.__init__(self)
      self.outer = outer

    def run(self):
      Control.reload_thread_lock.acquire()

      #before_id = 0
      #if len(self.outer.stored_items) > 0:
      #  before_id = self.outer.stored_items.get_visible(Control.list_visible_index).id

      self.outer.stored_items = utils.load(self.outer.notes_root, self.outer.recursive)
      self.outer.stored_items.sort_by_modification_date()

      nbr_objects = len(self.outer.stored_items)

      list_modes = self.outer.stored_items.modes()
      current_mode = list_modes[UserMode.current]
      
      #visible_counter = 0
      for i, note in enumerate(self.outer.stored_items):
        note.process_meta(i)

        if (current_mode == UserMode.ALL or current_mode in note.modes) and note.is_search_match(Control.get_last_regex()):
          note.visible(True)
          #if note.id == before_id:
          #  Control.list_visible_index = visible_counter
          #visible_counter += 1
        else:
          note.visible(False)

        if i % 100 == 0: # or i >= nbr_objects - 1:
          curses_view.complete_redraw(self.outer.stored_items)
      
      self.outer.stored_items.group_todo()
      curses_view.complete_redraw(self.outer.stored_items)
      Control.reload_thread_lock.release()

  @classmethod
  def main(self, stdscr, notes_root, recursive):

    utils.get_user_config()

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
      if TixMode.current == TixMode.LIST:
        curses_view.list_scroll_top -= curses_view.get_list_capacity()
        Control.list_visible_index -= curses_view.get_list_capacity()
        curses_view.adjust_scroll(len(self.stored_items))
      elif TixMode.current == TixMode.TAGS:
        curses_view.tags_scroll_top -= curses_view.get_list_capacity()
        Control.tags_visible_index -= curses_view.get_list_capacity()
        curses_view.adjust_scroll(len(self.stored_items.modes()))

    def keypress_list_pagedown():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        # TODO don't scroll if last item is in view
        curses_view.list_scroll_top += curses_view.get_list_capacity()
        Control.list_visible_index += curses_view.get_list_capacity()
        curses_view.adjust_scroll(len(self.stored_items))
      elif TixMode.current == TixMode.TAGS:
        curses_view.tags_scroll_top += curses_view.get_list_capacity()
        Control.tags_visible_index += curses_view.get_list_capacity()
        curses_view.adjust_scroll(len(self.stored_items.modes()))

    def keypress_select_first_in_view():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        i = Control.list_visible_index
        Control.list_visible_index = curses_view.list_scroll_top
        if i != Control.list_visible_index:
          curses_view.adjust_scroll(len(self.stored_items))
      elif TixMode.current == TixMode.TAGS:
        i = Control.tags_visible_index
        Control.tags_visible_index = curses_view.tags_scroll_top
        if i != Control.tags_visible_index:
          curses_view.adjust_scroll(len(self.stored_items.modes()))

    def keypress_select_last_in_view():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        i = Control.list_visible_index
        Control.list_visible_index = curses_view.list_scroll_top + curses_view.get_list_capacity() - 1
        if i != Control.list_visible_index:
          curses_view.adjust_scroll(len(self.stored_items))
      elif TixMode.current == TixMode.TAGS:
        i = Control.tags_visible_index
        Control.tags_visible_index = curses_view.tags_scroll_top + curses_view.get_list_capacity() - 1
        if i != Control.tags_visible_index:
          curses_view.adjust_scroll(len(self.stored_items.modes()))

    def keypress_select_middle_in_view():
      Control.reload_notes = False

      i_after = i_before = nbr_items = scroll_top = 0
      max_items_in_screen = curses_view.get_list_capacity() - 1

      if TixMode.current == TixMode.LIST:
        i_after = i_before = Control.list_visible_index
        scroll_top = curses_view.list_scroll_top
        nbr_items = len(self.stored_items)
      elif TixMode.current == TixMode.TAGS:
        i_after = i_before = Control.tags_visible_index
        scroll_top = curses_view.tags_scroll_top
        nbr_items = len(self.stored_items.modes())

      nbr_items_visible = min(nbr_items, nbr_items - scroll_top, max_items_in_screen)
      i_after = scroll_top + nbr_items_visible / 2

      if TixMode.current == TixMode.LIST:
        Control.list_visible_index = i_after
      elif TixMode.current == TixMode.TAGS:
        Control.tags_visible_index = i_after

      if i_before != i_after:
        curses_view.adjust_scroll(nbr_items)

    def keypress_select_next():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        Control.list_visible_index += 1
        curses_view.adjust_scroll(len(self.stored_items))
      elif TixMode.current == TixMode.TAGS:
        Control.tags_visible_index += 1
        nbr_modes = len(self.stored_items.modes())
        curses_view.adjust_scroll(nbr_modes)

    def keypress_select_prev():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        Control.list_visible_index -= 1
        curses_view.adjust_scroll(len(self.stored_items))
      elif TixMode.current == TixMode.TAGS:
        Control.tags_visible_index -= 1
        curses_view.adjust_scroll(len(self.stored_items.modes()))

    def keypress_select_last():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        Control.list_visible_index = len(self.stored_items) - 1
        curses_view.adjust_scroll(len(self.stored_items))
      elif TixMode.current == TixMode.TAGS:
        Control.tags_visible_index = len(self.stored_items.modes()) - 1
        curses_view.adjust_scroll(len(self.stored_items.modes()))

    def keypress_select_first():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        Control.list_visible_index = 0
        curses_view.list_scroll_top = 0
      elif TixMode.current == TixMode.TAGS:
        Control.tags_visible_index = 0
        curses_view.tags_scroll_top = 0

    def keypress_change_sorting_order():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        SortMode.current = (SortMode.current + 1) % len(SortMode.OPTIONS)
        if SortMode.current == SortMode.BY_SHUF:
          SortMode.current = (SortMode.current + 1) % len(SortMode.OPTIONS)

        item_id = self.stored_items.get_visible(Control.list_visible_index).id

        if SortMode.current == SortMode.BY_DATE:
          self.stored_items.sort_by_modification_date()
          self.stored_items.group_todo()
        elif SortMode.current == SortMode.BY_FILENAME:
          self.stored_items.sort_by_filename()

        new_index = 0
        for i, item in enumerate(self.stored_items):
          if item.id == item_id:
            new_index = i
            break

        Control.list_visible_index = new_index

    def keypress_shuf_order():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        SortMode.current = SortMode.BY_SHUF
        item_id = self.stored_items.get_visible(Control.list_visible_index).id
        random.shuffle(self.stored_items)
        new_index = 0
        for i, item in enumerate(self.stored_items):
          if item.id == item_id:
            new_index = i
            break

        Control.list_visible_index = new_index

    def keypress_insert():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        curses_view.end_curses()
        list_modes = self.stored_items.modes()
        current_mode = list_modes[UserMode.current]
        if current_mode == UserMode.ALL:
          current_mode = None
        else:
          current_mode = current_mode + "\n\n"
        n = utils.new_note(current_mode)
        curses_view.init_curses()
        if n:
          Control.list_visible_index = 0
          curses_view.adjust_scroll(len(self.stored_items))
          Control.reload_notes = True

    def keypress_toggle_filename_view():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        Control.list_view_mode += 1
        Control.list_view_mode = Control.list_view_mode % len(Control.LIST_VIEWS)

    def keypress_cycle_modes_reverse():
      keypress_cycle_modes(True)

    def keypress_cycle_modes(reverse=False):
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        list_modes = self.stored_items.modes()
        nbr_modes = len(list_modes)

        if nbr_modes == 0: return

        addition = 1 if not reverse else -1
        UserMode.current = (UserMode.current + addition) % nbr_modes
        
        for note in self.stored_items:
          if list_modes[UserMode.current] == UserMode.ALL or list_modes[UserMode.current] in note.modes:
            note.visible(True)
          else:
            note.visible(False)

    def keypress_read():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        curses_view.end_curses()
        filename = self.stored_items.get_visible(Control.list_visible_index).fullpath()
        utils.open_file_in_reader(filename)
        curses_view.init_curses()

    def keypress_enter():
      if TixMode.current == TixMode.LIST and len(self.stored_items) > 0:
        curses_view.end_curses()
        note_before = self.stored_items.get_visible(Control.list_visible_index)
        note_after = utils.edit_note(note_before)
        curses_view.init_curses()
        if note_before.text != note_after.text:
          Control.reload_notes = True
          Control.list_visible_index = 0
        else:
          Control.reload_notes = False
      elif TixMode.current == TixMode.TAGS:
        Control.reload_notes = False

        TixMode.current = TixMode.LIST

        if UserMode.current == Control.tags_visible_index:
          return
        else:
          UserMode.current = Control.tags_visible_index
          Control.list_visible_index = 0

        list_modes = self.stored_items.modes()
        for note in self.stored_items:
          if list_modes[UserMode.current] == UserMode.ALL or list_modes[UserMode.current] in note.modes:
            note.visible(True)
          else:
            note.visible(False)


    def keypress_cycle_tix_modes():
      Control.reload_notes = False

      nbr_modes = len(TixMode.OPTIONS)
      if nbr_modes == 0: return

      reverse = False
      addition = 1 if not reverse else -1
      TixMode.current = (TixMode.current + addition) % nbr_modes
      

    def keypress_switch_to_list_mode():
      Control.reload_notes = False
      TixMode.current = TixMode.LIST

    def keypress_switch_to_tags_mode():
      Control.reload_notes = False
      TixMode.current = TixMode.TAGS

    def pressed_slash():
      Control.reload_notes = False
      if TixMode.current == TixMode.LIST:
        Control.reload_thread_lock.acquire()

        def validator(c):
          if c == 27:
            # ctrl A >then> ctrl K
            # regex = None
            return 7
          elif c == 10:
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
        try:
          curses.curs_set(1)
        except curses.error: # iphone
          pass
        Control.current_regex_index = len(Control.regex_patterns)
        curses_view.footer_pad.clear()
        CursesView.add_str(curses_view.footer_pad, curses_view.search_prompt)
        self.is_searching = True
        regex = curses_view.search_textbox.edit(validator)
        self.is_searching = False
        try:
          curses.curs_set(0)
        except curses.error: # iphone
          pass
        if regex != None:
          regex = regex[len(curses_view.search_prompt):]
          if regex.strip(): Control.regex_patterns.append(regex)
          Control.list_visible_index = 0
          curses_view.adjust_scroll(len(self.stored_items))

          list_modes = self.stored_items.modes()
          current_mode = list_modes[UserMode.current]
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
      ord('l'): keypress_switch_to_tags_mode,
      ord('g'): keypress_select_first,
      ord('G'): keypress_select_last,
      ord('a'): keypress_insert,
      ord('r'): keypress_read,
      ord('n'): keypress_cycle_modes,
      ord('p'): keypress_cycle_modes_reverse,
      ord('\t'): keypress_cycle_tix_modes,
      9: keypress_cycle_tix_modes, # = TAB
      #353: keypress_cycle_modes_reverse, # = SHIFT + TAB
      ord('f'): keypress_toggle_filename_view,
      ord('s'): keypress_change_sorting_order,
      ord('S'): keypress_shuf_order,
      ord('/'): pressed_slash,
      10: keypress_enter,
      curses.KEY_ENTER: keypress_enter,
      curses.KEY_DOWN: keypress_select_next,
      curses.KEY_UP: keypress_select_prev,
      curses.KEY_HOME: keypress_select_first,
      curses.KEY_END: keypress_select_last,
      curses.KEY_NPAGE: keypress_list_pagedown,
      curses.KEY_PPAGE: keypress_list_pageup,
      curses.KEY_LEFT: keypress_switch_to_list_mode,
      curses.KEY_RIGHT: keypress_switch_to_tags_mode,
    })
    #}}}

    while True:
      curses_view.update_screen_size()
      curses_view.recalculate_widths()
      curses_view.create_footer_pad()

      if Control.reload_notes:
        if not Control.reload_thread_lock.locked():
          t = self.Loader(self)
          t.start()
      elif not Control.reload_thread_lock.locked():
        curses_view.complete_redraw(self.stored_items)

      Control.reload_notes = False
      c = curses_view.keyboard_pad.getch()

      if c == ord('q'): break
      f = key_to_action.get(c)
      if f: f()

    curses_view.end_curses()
