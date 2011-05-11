from collections import namedtuple
import os
import re
import tempfile
import datetime
import textwrap
import subprocess
import ConfigParser
import shutil
from note import Note, NoteList

TAG_REGEX = r'#[^\s:;#=\(\)\"]{1,50}'

HOME_DIR = os.getenv('USERPROFILE') or os.getenv('HOME')

DEFAULT_USER_CONFIGURATIONS = {
  'EDITOR': 'vi',
  'READER': 'less',
  'TIXPATH': os.path.join(HOME_DIR, 'tix'),
  'NOTEPATH': [os.path.join(HOME_DIR, 'tix')],
}

user_configurations = DEFAULT_USER_CONFIGURATIONS

def load(root_dir, recursive):
  if not os.path.exists(root_dir) or not os.path.isdir(root_dir):
    return NoteList()

  stored_list = NoteList()

  # look at current dir if config's path is empty:
  if not user_configurations['NOTEPATH']:
    user_configurations['NOTEPATH'].add(root_dir)

  if recursive:
    for dir_path in user_configurations['NOTEPATH']:
      if not os.path.exists(dir_path):
        continue
      for file_path, dirs, files in os.walk(dir_path):
        if '.git' in file_path.split(os.sep):
          continue
        stored_list += read_notes(file_path, files)
        continue
  else:
    for file_path in user_configurations['NOTEPATH']:
      if not os.path.exists(file_path):
        continue
      files = os.listdir(file_path)
      stored_list += read_notes(file_path, files)
  return stored_list

def read_notes(path, filenames, firstline_only=False):
  notes = NoteList()
  for filename in filenames:
    if not re.search(r'.*(txt|md|markdown)$', filename):
      continue
    full_path = os.path.join(path, filename)
    if os.path.isfile(full_path):
      with open(full_path, 'r') as f:
        if firstline_only:
          text = f.readline()
        else:
          text = f.read()
        #if not is_binary(text):
        notes.append(Note(filename, path, text))
  return notes


def open_file_in_editor(file_name):
  """ start editor with file_name """
  global user_configurations
  subprocess.call(['%s "%s"' % (user_configurations['EDITOR'], file_name)], shell=True)

def open_file_in_reader(file_name):
  """ start reader with file_name """
  global user_configurations
  subprocess.call(['%s "%s"' % (user_configurations['READER'], file_name)], shell=True)

def edit_note(note):
  fullpath = os.path.join(note.path, note.filename)

  #text_before_edit = note.text
  open_file_in_editor(fullpath)
  with open(fullpath, 'r') as f:
    note_content = f.read()
    #if note_content == text_before_edit:
    #  return None
    n = Note(note.filename, note.path, note_content)
    return n
  return None

#def archive_note(filename):
#  directory = os.path.join(user_configurations['TIXPATH'], 'archive')

def new_note(initial_text=None):
  directory = user_configurations['TIXPATH']
  
  now = datetime.datetime.now()
  t = now.strftime("%Y-%m-%d-%H-%M-%S")

  import time

  epoch_seconds = time.time()
  #secs_whole = int(epoch_seconds)
  #secs_fraction = int((epoch_seconds - secs_whole) * 100)
  #timestamp = "%s--%s.%s" % (t, secs_whole, secs_fraction)
  timestamp = "%s-%s" % (epoch_seconds, t)

  new_filename = "tix-%s.txt" % timestamp
  new_filepath = os.path.join(directory, new_filename)

  #if not os.path.exists(directory):
  #  os.mkdir(directory)
  if initial_text:
    with open(new_filepath, 'w') as f:
      f.write(initial_text)
  open_file_in_editor(new_filepath)
  #os.rmdir(directory)
  if not os.path.exists(new_filepath):
    return None

  with open(new_filepath, 'r') as f:
    note_content = f.read()
    if note_content.strip() == "":
      return None

    n = Note(new_filename, directory, note_content)
    return n

def get_modification_date(file_path):
  now = datetime.datetime.now()
  file_datetime = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
  return file_datetime

def get_all_tags(txt):
  return set([m.lower() for m in re.findall(TAG_REGEX, txt, re.LOCALE)])
  #return set(re.findall(r'#[\w-\']+', txt, re.LOCALE))

def log(message):
  with open('tix.log', 'a') as f:
    f.write("Log message: %s\n" % message)

def get_number_of_lines(text, note_width):
  lines = text.splitlines()
  number_of_lines = 0
  for line in lines:
    wrapped_lines = textwrap.wrap(line, note_width,
        replace_whitespace=True,
        drop_whitespace=True)
    number_of_lines += len(wrapped_lines) or 1
  return number_of_lines

def get_user_config():
  config_path = os.path.join(user_configurations['TIXPATH'], 'tix.cfg')
  config_parser = ConfigParser.ConfigParser()

  if os.path.exists(config_path):
    config_parser.read(config_path)
    global user_configurations

    try:
      user_configurations['EDITOR'] = config_parser.get('general', 'editor')
    except ConfigParser.NoOptionError as e:
      pass

    try:
      user_configurations['READER'] = config_parser.get('general', 'reader')
    except ConfigParser.NoOptionError as e:
      pass

    try:
      user_configurations['TIXPATH'] = config_parser.get('general', 'tixpath').replace(r'~', HOME_DIR)
    except ConfigParser.NoOptionError as e:
      pass

    try:
      path = config_parser.get('general', 'notepath').replace(r'~', HOME_DIR).split(',')
      user_configurations['NOTEPATH'] = set([p.split(':')[0].strip() for p in path])
      if '' in user_configurations['NOTEPATH']:
        user_configurations['NOTEPATH'].remove('')
      if len(user_configurations['NOTEPATH']) == 0:
        user_configurations['NOTEPATH'] = DEFAULT_USER_CONFIGURATIONS['NOTEPATH']
    except KeyError as e:
      raise e
    except ConfigParser.NoOptionError as e:
      pass

  else:
    if not os.path.exists(user_configurations['TIXPATH']):
      os.mkdir(user_configurations['TIXPATH'])

    print('Edit "%s" to change your default editor' % config_path)
    config_parser.add_section('general')
    config_parser.set('general', 'editor',   user_configurations['EDITOR'])
    config_parser.set('general', 'reader',   user_configurations['READER'])
    config_parser.set('general', 'tixpath',  user_configurations['TIXPATH'])
    config_parser.set('general', 'notepath', ','.join(user_configurations['NOTEPATH']))
    with open(config_path, 'wb') as f:
      config_parser.write(f)

def is_binary(string):
  if not string or not '\0' in string:
    return False
  else:
    return True

def get_first_line(string):
  lines = list()
  for s in string.splitlines():
    s = re.sub(TAG_REGEX, '', s).strip()
    if s:
      lines.append(s)
      if len(lines) > 1: break
  first_line = os.linesep.join(lines)
  first_line = re.sub(r'[\t ]+', ' ', first_line)
  first_line = re.sub(r'[\n\r].*', '', first_line)
  
  return first_line
