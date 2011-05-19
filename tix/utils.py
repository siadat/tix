import os
import re
import time
import datetime
import textwrap
import subprocess
import ConfigParser
from note import Note

#TODO_REGEX = r'\b(TODO|DEADLINE)\b'
#NOT_TODO_REGEX = r'\b(NOTODO|NODEADLINE)\b'

# FIXME compiled regular expressions are faster

FILENAME_WHITELIST_REGEX = r'.*(txt|md|markdown)$'

HOME_DIR = os.getenv('USERPROFILE') or os.getenv('HOME')

DEFAULT_USER_CONFIGURATIONS = {
  'EDITOR': 'vi',
  'READER': 'less',
  'TIXPATH': os.path.join(HOME_DIR, 'tix'),
  'NOTEPATH': [os.path.join(HOME_DIR, 'tix')],
  'TAG_REGEX': r'[#][^\s;#=\(\)\"]{1,50}',
  'IMPORTANT_REGEX': r'\b(TODO|DEADLINE)\b',
  'UNIMPORTANT_REGEX': r'\b(NOTODO|NODEADLINE)\b',
}

user_configurations = DEFAULT_USER_CONFIGURATIONS

def open_file_in_editor(file_name):
  """ start editor with file_name """
  global user_configurations
  if True:
    #alternative_editors = ['gedit', 'leafpad', 'notepad', 'nano', ]
    command = user_configurations['EDITOR'].replace('%f', '"%s"' % file_name)
    try:
      subprocess.call([command], shell=True)
    except OSError:
      pass
  else:
    fulltext = ""
    with open(file_name, 'r') as f:
      fulltext = f.read()
    #gui = GtkMain()
    #gui.show_text_editor(fulltext)

def open_file_in_reader(file_name):
  """ start reader with file_name """
  global user_configurations
  command = user_configurations['READER'].replace('%f', '"%s"' % file_name)
  try:
    subprocess.call([command], shell=True)
  except OSError:
    pass

def generate_filename():
  directory = user_configurations['TIXPATH']
  epoch_seconds = time.time()
  now = datetime.datetime.now()
  t = now.strftime("%Y-%m-%d-%H-%M-%S")
  timestamp = "%s-%s" % (epoch_seconds, t)
  new_filename = "tix-%s.txt" % timestamp
  return new_filename

def new_note(initial_text=None):
  directory = user_configurations['TIXPATH']
  new_filename = generate_filename()
  new_filepath = os.path.join(directory, new_filename)

  if initial_text:
    with open(new_filepath, 'w') as f:
      f.write(initial_text)
  open_file_in_editor(new_filepath)
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
  return set([m.lower() for m in re.findall(user_configurations['TAG_REGEX'], txt, re.L | re.U)])


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
      user_configurations['TAG_REGEX'] = config_parser.get('general', 'tag_regex')
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
    config_parser.set('general', 'editor %f',   user_configurations['EDITOR'])
    config_parser.set('general', 'reader %f',   user_configurations['READER'])
    config_parser.set('general', 'tixpath',  user_configurations['TIXPATH'])
    config_parser.set('general', 'notepath', ','.join(user_configurations['NOTEPATH']))
    config_parser.set('general', 'tag_regex',  user_configurations['TAG_REGEX'])
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
    s = re.sub(user_configurations['TAG_REGEX'], '', s).strip()
    if s:
      lines.append(s)
      if len(lines) > 1: break
  first_line = os.linesep.join(lines)
  first_line = re.sub(r'[\t ]+', ' ', first_line)
  first_line = re.sub(r'[\n\r].*', '', first_line)
  
  return first_line

def log(message):
  with open('tix.log', 'a') as f:
    f.write("Log message: %s\n" % message)
