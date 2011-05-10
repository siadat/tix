import curses

# Unicode:
import locale
locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

class CursesView(object):

  def __init__(self):
    self.MAX_NLINE = 100
    self.LIST_ITEM_MAX_HEIGHT = 2

    self.margin_top = 0
    self.margin_left = 0
    self.margin_bottom = 1
    self.note_padding_left = 1
    self.note_padding_right = 1
    self.note_width = 80
    self.list_width = 40
    self.list_item_height = 1
    self.separator_thickness = 1

    self.list_scroll_top = 0
    self.note_scroll_top = 0

    self.search_prompt = "/"
    self.screen = curses.initscr()

    self.update_screen_size()
    self.init_curses()
    self.keyboard_pad = curses.newpad(1,1)

    self.footer_pad = None
    self.search_textbox = None
    self.current_note_pad = None

    self.WELCOME = """
TIX - text file manager
=======================

Quick start:

  <q> to quit
  <a> to quickly add a note
  <ENTER> to edit a note
  </> to start searching
"""

  def create_footer_pad(self):
    self.footer_pad = self.screen.subpad(
        1, self.screen_yx[1],
        self.screen_yx[0] - self.margin_bottom,
        self.margin_left)

  def create_note_pad(self):
    try:
      x = self.note_width
      y = self.get_list_capacity() + 1000 # + self.MAX_NLINE
      self.current_note_pad = curses.newpad(y, x)
      self.current_note_pad.idlok(True)
      self.current_note_pad.scrollok(True)
    except curses.error as e:
      self.end_curses()
      print("Resize your window to add more width, then start lil again.")
      exit()

  def recalculate_note_width(self):
    self.note_width = self.screen_yx[1] \
        - self.list_width - self.margin_left \
        - self.note_padding_left - self.note_padding_right \
        - self.separator_thickness

    min_note_width = 20
    max_note_width = min(80, self.screen_yx[1] - self.margin_left - 10)

    if self.note_width < min_note_width: self.note_width = min_note_width
    if self.note_width > max_note_width: self.note_width = max_note_width

  def update_screen_size(self):
    self.screen_yx = self.screen.getmaxyx()

  def init_curses(self):
    curses.noecho()
    curses.cbreak()
    curses.curs_set(False)
    curses.start_color()
    curses.use_default_colors()
    self.screen.keypad(1)
    self.screen.idlok(True)
    self.screen.scrollok(True)

  def end_curses(self):
    curses.nocbreak();
    curses.echo()
    curses.endwin()
    self.screen.keypad(False);

  def get_list_capacity(self):
    return self.screen_yx[0] / self.list_item_height - (self.margin_top + self.margin_bottom)

  def draw_ruler(self):
    return
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_WHITE)
    for i in range(0, self.screen_yx[0]):
      self.add_ch(self.screen, '~',# curses.ACS_BULLET, # curses.ACS_VLINE,
          (i, self.margin_left + self.list_width),
          curses.A_DIM)

      #CursesView.add_ch(self.screen, ' ',
      #    (i, self.margin_left + self.list_width + self.note_width + 3),
      #    curses.A_DIM | curses.A_REVERSE)

  def adjust_scroll(self, nbr_items, list_visible_index):
    if self.list_scroll_top < 0:
      self.list_scroll_top = 0

    if self.note_scroll_top < 0:
      self.note_scroll_top = 0

    if nbr_items > 0:
      if list_visible_index < 0:
        list_visible_index = 0
      elif list_visible_index > nbr_items - 1:
        list_visible_index = nbr_items - 1

    note_top_y = self.margin_top + list_visible_index * self.list_item_height
    note_bottom_y = note_top_y + self.list_item_height + self.margin_bottom

    if note_bottom_y >= self.screen_yx[0] + self.list_scroll_top:
      self.list_scroll_top = note_bottom_y - self.screen_yx[0]
    elif note_top_y < self.list_scroll_top:
      self.list_scroll_top = note_top_y - self.margin_top

    return list_visible_index

  @staticmethod
  def add_str(win_or_pad, text, flags=0):
    try:
      pos_yx = (0, 0)
      win_or_pad.addstr(pos_yx[0], pos_yx[1], text, flags)
    except curses.error as e:
      #raise(e)
      pass

  @staticmethod
  def add_ch(win_or_pad, ch, pos_yx, flags=0):
    try:
      win_or_pad.addch(pos_yx[0], pos_yx[1], ch, flags)
    except curses.error as e:
      #raise(e)
      pass

  def complete_redraw(self, stored_items):
    from control import Control
    from note import NoteList
    
    if not isinstance(stored_items, NoteList):
      raise TypeError, stored_items

    nbr_objects = len(stored_items)
    self.screen.clear()
    Control.list_visible_index = self.adjust_scroll(nbr_objects, Control.list_visible_index)
    self.draw_ruler()
    self.draw_footer(stored_items)
    self.draw_stored_items(stored_items)
    self.screen.refresh()

  def draw_footer(self, notes_list):
    from control import Control, TixMode, UserMode
    import utils

    flags = 0 # curses.A_REVERSE

    if notes_list.has_note():
      current_note = notes_list.get_visible(Control.list_visible_index)
      viewing_filename = current_note.fullpath()
      all_modes = notes_list.modes()

      showing_user_mode = all_modes[UserMode.current_user_mode]
      if len(current_note.modes) > 0:
        text = 'Showing %s "%s" [%s-mode] ' % (showing_user_mode, viewing_filename, TixMode.TIX_MODES[TixMode.current_tix_mode]) # " ".join(current_note.modes),
      else:
        text = 'Showing %s "%s" [%s-mode] ' % (showing_user_mode, viewing_filename, TixMode.TIX_MODES[TixMode.current_tix_mode])
    else:
      text = 'No file [%s-mode]' % TixMode.TIX_MODES[TixMode.current_tix_mode]

    text = text.ljust(self.screen_yx[1])
    self.add_str(self.footer_pad, text, flags)
    self.search_textbox = curses.textpad.Textbox(self.footer_pad)

  def draw_stored_list(self, stored_items):
    from control import Control, TixMode
    y = self.margin_top - self.list_scroll_top
    i = -1
    for stored_item in stored_items:
      if not stored_item.is_shown:
        continue
      i += 1
      if self.list_item_height > self.LIST_ITEM_MAX_HEIGHT:
        self.list_item_height = self.LIST_ITEM_MAX_HEIGHT

      if y < 0 or y + self.list_item_height + self.margin_bottom > self.screen_yx[0]:
        y += self.list_item_height
        continue

      indent_level = 0

      pad_h = self.list_item_height - 1
      pad_w = self.list_width - indent_level - 1
      pad_top = y

      pad_item = self.screen.subpad(
          pad_h, pad_w,
          pad_top, self.margin_left + indent_level)

      first_line = ""
      if Control.list_view_mode == Control.LIST_VIEW_FILENAME:
        first_line = stored_item.filename[:self.list_width]
      elif Control.list_view_mode == Control.LIST_VIEW_FIRSTLINE:
        first_line = stored_item.first_line
        if not first_line.strip():
          first_line = "(empty)"
      elif Control.list_view_mode == Control.LIST_VIEW_TAGS:
        first_line = " ".join(stored_item.modes)
        if not first_line.strip():
          first_line = "-"

      first_line = first_line[:self.list_width - 1].strip()

      flags = 0

      if stored_item.is_todo:
        flags |= curses.A_BOLD

      if i == Control.list_visible_index:
        if TixMode.current_tix_mode == TixMode.LIST_TIX_MODE:
          flags |= curses.A_BOLD | curses.A_REVERSE
        else:
          flags |= curses.A_UNDERLINE

        self.add_str(pad_item, first_line.ljust(pad_w), flags)
      else:
        self.add_str(pad_item, first_line.ljust(pad_w), flags)

      y += self.list_item_height

  def draw_note(self, stored_item):
    return
    max_number_of_chars = self.MAX_NLINE * 80
    self.add_str(self.current_note_pad, stored_item.text[:max_number_of_chars])
    self.current_note_pad.scroll(self.note_scroll_top)

  def draw_stored_items(self, stored_items):
    from control import Control

    if len(stored_items) == 0:
      self.add_str(self.current_note_pad, self.WELCOME)
    else:
      self.draw_stored_list(stored_items)
      item = stored_items.get_visible(Control.list_visible_index)
      self.draw_note(item)

    try:
      self.current_note_pad.overwrite(self.screen,
          0,
          0,
          self.margin_top,
          self.margin_left + self.list_width + 2,
          self.screen_yx[0] - self.margin_top - self.margin_bottom - 1,
          self.margin_left + self.list_width + self.note_width + 1)
    except Exception as e:
      raise e
