import curses

# Unicode:
import locale
locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

class TextWithFormat(object):
  def __init__(self, str, flags, color_pair=0):
    self.str = str
    self.flags = flags
    self.color_pair = color_pair

  def write(self, win, max_width):
    if curses.has_colors():
      c = curses.color_pair(self.color_pair)
    else:
      c = 0
    CursesView.add_str(win, self.str, self.flags | c, max_width)

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
    self.list_width = 40 * 2
    self.list_item_height = 1
    self.separator_thickness = 1

    self.list_scroll_top = 0
    self.tags_scroll_top = 0
    self.note_scroll_top = 0

    self.search_prompt = "/"
    self.screen = curses.initscr()

    self.update_screen_size()
    self.init_curses()
    self.keyboard_pad = curses.newpad(1,1)
    self.keyboard_pad.keypad(1)

    self.footer_pad = None
    self.search_textbox = None
    self.current_note_pad = None


    if curses.has_colors():
      curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
      curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
      curses.init_pair(3, curses.COLOR_YELLOW, -1)
      curses.init_pair(4, curses.COLOR_RED, -1)
      curses.init_pair(5, curses.COLOR_BLUE, -1)
      curses.init_pair(6, curses.COLOR_CYAN, -1)

    self.COLOR_DEFAULT = 0
    self.COLOR_WHITE_ON_BLUE = 1
    self.COLOR_RED_ON_WHITE = 2
    self.COLOR_YELLOW = 3
    self.COLOR_RED = 4
    self.COLOR_BLUE = 5
    self.COLOR_CYAN = 6

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

  def recalculate_widths(self):
    
    self.list_width = self.screen_yx[1]

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

  # TODO rename to 'start_curses'
  def init_curses(self):
    curses.noecho()
    curses.cbreak()

    try:
      curses.curs_set(0)
    except curses.error: # iphone
      pass

    if curses.has_colors():
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

  def adjust_scroll(self, nbr_items):
    from control import TixMode, Control

    if TixMode.current == TixMode.LIST:
      if nbr_items > 0:
        if Control.list_visible_index < 0:
          Control.list_visible_index = 0
        elif Control.list_visible_index > nbr_items - 1:
          Control.list_visible_index = nbr_items - 1

      note_top_y = self.margin_top + Control.list_visible_index * self.list_item_height
      note_bottom_y = note_top_y + self.list_item_height + self.margin_bottom

      if self.list_scroll_top < 0:
        self.list_scroll_top = 0
      if note_bottom_y >= self.screen_yx[0] + self.list_scroll_top:
        self.list_scroll_top = note_bottom_y - self.screen_yx[0]
      elif note_top_y < self.list_scroll_top:
        self.list_scroll_top = note_top_y - self.margin_top

      return Control.list_visible_index
    elif TixMode.current == TixMode.TAGS:
      if nbr_items > 0:
        if Control.tags_visible_index < 0:
          Control.tags_visible_index = 0
        elif Control.tags_visible_index > nbr_items - 1:
          Control.tags_visible_index = nbr_items - 1

        note_top_y = self.margin_top + Control.tags_visible_index * self.list_item_height
        note_bottom_y = note_top_y + self.list_item_height + self.margin_bottom

        if self.tags_scroll_top < 0:
          self.tags_scroll_top = 0
        if note_bottom_y >= self.screen_yx[0] + self.tags_scroll_top:
          self.tags_scroll_top = note_bottom_y - self.screen_yx[0]
        elif note_top_y < self.tags_scroll_top:
          self.tags_scroll_top = note_top_y - self.margin_top
        return Control.tags_visible_index

  @staticmethod
  def add_str(win_or_pad, text, flags=0, max_width=10000, pos_yx=None):
    try:
      if not pos_yx:
        win_or_pad.addnstr(text, max_width, flags)
      else:
        win_or_pad.addnstr(pos_yx[0], pos_yx[1], text, max_width, flags)
    except curses.error as e:
      pass

  @staticmethod
  def add_ch(win_or_pad, ch, pos_yx, flags=0):
    try:
      win_or_pad.addch(pos_yx[0], pos_yx[1], ch, flags)
    except curses.error as e:
      pass

  def complete_redraw(self, stored_items):
    from control import Control, TixMode
    from note import NoteList
    
    if not isinstance(stored_items, NoteList):
      raise TypeError, stored_items

    self.screen.clear()

    self.draw_footer(stored_items)

    if TixMode.current == TixMode.LIST:
      nbr_objects = len(stored_items)
      self.adjust_scroll(nbr_objects)
      self.draw_stored_items(stored_items)
    elif TixMode.current == TixMode.TAGS:
      nbr_objects = len(stored_items.modes())
      self.adjust_scroll(nbr_objects)
      self.draw_tags(stored_items)

    self.screen.refresh()

  def draw_footer(self, notes_list):
    from control import Control, TixMode, UserMode
    flags = curses.A_REVERSE
    
    if TixMode.current == TixMode.LIST:
      if notes_list.has_note():
        current_note = notes_list.get_visible(Control.list_visible_index)
        viewing_filename = current_note.fullpath()
        all_modes = notes_list.modes()
        showing_user_mode = all_modes[UserMode.current]

        text = 'Viewing %s "%s" [%s-mode] ' % \
          (showing_user_mode, viewing_filename, TixMode.OPTIONS[TixMode.current])
      else:
        text = 'No file [%s-mode]' % TixMode.OPTIONS[TixMode.current]
    elif TixMode.current == TixMode.TAGS:
      text = 'Viewing tags'

    text = text.ljust(self.screen_yx[1])
    CursesView.add_str(self.footer_pad, text, flags, self.list_width, (0,0))
    self.search_textbox = curses.textpad.Textbox(self.footer_pad)

  def draw_tags(self, stored_items):
    from control import Control, TixMode, UserMode

    y = self.margin_top - self.tags_scroll_top
    i = -1

    all_modes = stored_items.modes()
    showing_user_mode = all_modes[UserMode.current]

    for mode in all_modes:
      i += 1
      if self.list_item_height > self.LIST_ITEM_MAX_HEIGHT:
        self.list_item_height = self.LIST_ITEM_MAX_HEIGHT

      if y < 0 or y + self.list_item_height + self.margin_bottom > self.screen_yx[0]:
        y += self.list_item_height
        continue

      pad_h = self.list_item_height - 1
      pad_w = self.list_width
      pad_top = y

      pad_item = self.screen.subpad(
          pad_h, pad_w,
          pad_top, self.margin_left)

      flags = 0


      list_item_texts = []
      item_line = mode

      if i == Control.tags_visible_index:
        flags |= curses.A_REVERSE
        list_item_texts.append(TextWithFormat(item_line, flags, self.COLOR_DEFAULT))
      else:
        list_item_texts.append(TextWithFormat(item_line, flags, self.COLOR_CYAN))

      for t in list_item_texts:
        t.write(pad_item, self.list_width)
        pad_item.addch(' ')

      y += self.list_item_height

  def draw_stored_list(self, stored_items):
    from control import Control, TixMode, UserMode
    y = self.margin_top - self.list_scroll_top
    i = -1

    all_modes = stored_items.modes()
    showing_user_mode = all_modes[UserMode.current]

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
      pad_w = self.list_width - indent_level
      pad_top = y

      try:
        pad_item = self.screen.subpad(
            pad_h, pad_w,
            pad_top, self.margin_left + indent_level)
      except curses.error as e:
        y += self.list_item_height
        continue

      flags = 0

      if i == Control.list_visible_index:
        if TixMode.current == TixMode.LIST:
          flags |= curses.A_REVERSE
        elif TixMode.current == TixMode.TAGS:
          flags |= curses.A_UNDERLINE

        if stored_item.is_todo:
          flags |= curses.A_BOLD

      list_item_texts = []
      item_line = ""
      if Control.list_view_mode == Control.LIST_VIEW_FILENAME:
        item_line = stored_item.fullpath()[:self.list_width]
        list_item_texts.append(TextWithFormat(item_line, flags, self.COLOR_DEFAULT))
      elif Control.list_view_mode == Control.LIST_VIEW_FIRSTLINE:
        first_line = stored_item.first_line
        #modes = " ".join(stored_item.modes)
        modes = " ".join([m for m in stored_item.modes if m != all_modes[UserMode.current]])

        if modes.strip():
          if len(modes) > self.list_width/3:
            modes = modes[:self.list_width/3-3] + "..."

          if stored_item.is_todo:
            list_item_texts.append(TextWithFormat(modes, flags, self.COLOR_CYAN))
          else:
            list_item_texts.append(TextWithFormat(modes, flags, self.COLOR_CYAN))
        else:
          modes = ""

        first_line = stored_item.first_line[:self.list_width - len(modes)]
        if not first_line.strip():
          first_line = "[empty]"
        list_item_texts.append(TextWithFormat(first_line, flags, self.COLOR_DEFAULT))
      
      if stored_item.is_todo and Control.list_view_mode != Control.LIST_VIEW_FILENAME:
        list_item_texts.insert(0, TextWithFormat('...', flags | curses.A_BOLD, self.COLOR_DEFAULT))

      if i == Control.list_visible_index:
        t = " ".join([ii.str for ii in list_item_texts])
        CursesView.add_str(pad_item, t.ljust(pad_w), flags, pad_w)
      else:
        for t in list_item_texts:
          t.write(pad_item, self.list_width)
          pad_item.addch(' ')

      y += self.list_item_height

  def draw_note(self, stored_item):
    max_number_of_chars = self.MAX_NLINE * 80
    CursesView.add_str(self.current_note_pad, stored_item.text[:max_number_of_chars])
    self.current_note_pad.scroll(self.note_scroll_top)

  def draw_stored_items(self, stored_items):
    from control import Control
    if len(stored_items) > 0:
      self.draw_stored_list(stored_items)
